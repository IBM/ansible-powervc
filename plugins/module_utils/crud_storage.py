#!/usr/bin/python

import requests


def _extract_error_message(response):
    '''Extract human-readable error details from PowerVC / Cinder API responses.'''
    try:
        err_json = response.json()
        if isinstance(err_json, dict):
            # Cinder standard error formats: {"badRequest": {"message": "..."}, "computeFault": {"message": "..."}}
            for key in ("badRequest", "computeFault", "itemNotFound", "forbidden", "unauthorized", "overLimit", "error"):
                if key in err_json and isinstance(err_json[key], dict) and "message" in err_json[key]:
                    return err_json[key]["message"]
            if "message" in err_json:
                return str(err_json["message"])
            if "error_message" in err_json:
                return str(err_json["error_message"])
            if "description" in err_json:
                return str(err_json["description"])
    except Exception:
        pass
    return response.text


def get_headers(authtoken):
    return {
        "X-Auth-Token": authtoken,
        "Content-Type": "application/json",
        "Openstack-API-Version": "volume latest",
    }


def get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id):
    all_endpoints = connectn.identity.endpoints()
    services = connectn.identity.services()
    service_map = {service.id: service.type for service in services}
    service_id = next(
        (sid for sid, name in service_map.items() if name == service_name), None
    )
    if not service_id:
        mod.fail_json(msg=f"No service found: {service_name}")
    endpoint = next(
        (ep for ep in all_endpoints if ep.service_id == service_id), None
    )
    if not endpoint:
        mod.fail_json(msg=f"No endpoint found for {service_name}")
    return endpoint.url.replace("%(tenant_id)s", tenant_id)


def storage_ops(
    module,
    endpoint,
    authtoken,
    tenant_id,
    verify,
    state,
    storage_id=None,
    body=None,
    detail=False,
):
    headers = get_headers(authtoken)
    if state == "absent":
        if not storage_id:
            module.fail_json(msg="host name from storage specific metadata is required")
        url = f"{endpoint}/os-hosts/{storage_id}"
        response = requests.delete(url, headers=headers, verify=verify)
        if response.status_code == 204:
            return dict(changed=True, msg="Storage remove operation initiated successfully")
        err_msg = _extract_error_message(response)
        module.fail_json(
            msg=f"Failed to remove the storage: {err_msg}",
            status_code=response.status_code,
            response=response.text,
        )
    if state == "present" and body and not storage_id:
        url = f"{endpoint}/os-hosts"
        response = requests.post(
            url,
            headers=headers,
            json=body,
            verify=verify,
        )
        if response.status_code in [200, 202]:
            return dict(
                changed=True,
                msg="Storage registered successfully",
                result=response.json(),
            )
        err_msg = _extract_error_message(response)
        module.fail_json(
            msg=f"Failed to add storage: {err_msg}",
            status_code=response.status_code,
            response=response.text,
        )
    if state == "present" and storage_id and body:
        url = f"{endpoint}/os-hosts/{storage_id}"
        response = requests.put(url, headers=headers, json=body, verify=verify)
        if response.status_code == 200:
            return dict(changed=True, msg="Updated", result=response.json())
        err_msg = _extract_error_message(response)
        module.fail_json(
            msg=f"Failed to update storage: {err_msg}",
            status_code=response.status_code,
            response=response.text,
        )
    if state == "present" and storage_id:
        if detail:
            # Query /storage-providers/detail and filter for the target storage_id
            url = f"{endpoint}/storage-providers/detail"
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code == 200:
                try:
                    data = response.json()
                    providers = data.get("storage_providers", [])
                    matched = next(
                        (
                            sp for sp in providers
                            if str(sp.get("id")) == str(storage_id)
                            or sp.get("storage_hostname") == storage_id
                            or sp.get("service", {}).get("host") == storage_id
                            or sp.get("service", {}).get("host_display_name") == storage_id
                        ),
                        None,
                    )
                    if matched is not None:
                        return dict(changed=False, result={"storage_provider": matched})
                except Exception:
                    pass
            # If not found or storage-providers endpoint unavailable, fallback to /os-hosts/{storage_id}
            fallback_url = f"{endpoint}/os-hosts/{storage_id}"
            fb_response = requests.get(fallback_url, headers=headers, verify=verify)
            if fb_response.status_code == 200:
                return dict(changed=False, result=fb_response.json())
            err_msg = _extract_error_message(fb_response if fb_response.status_code != 200 else response)
            module.fail_json(
                msg=f"Failed to fetch storage details: {err_msg}",
                status_code=fb_response.status_code if fb_response.status_code != 200 else response.status_code,
                response=fb_response.text if fb_response.status_code != 200 else response.text,
            )
        else:
            url = f"{endpoint}/os-hosts/{storage_id}"
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code != 200:
                err_msg = _extract_error_message(response)
                module.fail_json(
                    msg=f"Failed to fetch storage details: {err_msg}",
                    status_code=response.status_code,
                    response=response.text,
                )
            return dict(changed=False, result=response.json())
    if state == "present":
        if detail:
            url = f"{endpoint}/storage-providers/detail"
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code == 200:
                return dict(changed=False, result=response.json())
            # Fallback to /os-hosts if /storage-providers/detail fails
            fallback_url = f"{endpoint}/os-hosts"
            fb_response = requests.get(fallback_url, headers=headers, verify=verify)
            if fb_response.status_code == 200:
                return dict(changed=False, result=fb_response.json())
            err_msg = _extract_error_message(fb_response if fb_response.status_code != 200 else response)
            module.fail_json(
                msg=f"Failed to fetch storage details: {err_msg}",
                status_code=fb_response.status_code if fb_response.status_code != 200 else response.status_code,
                response=fb_response.text if fb_response.status_code != 200 else response.text,
            )
        else:
            url = f"{endpoint}/os-hosts"
            response = requests.get(url, headers=headers, verify=verify)
            if response.status_code != 200:
                err_msg = _extract_error_message(response)
                module.fail_json(
                    msg=f"Failed to fetch storage details: {err_msg}",
                    status_code=response.status_code,
                    response=response.text,
                )
            return dict(changed=False, result=response.json())
