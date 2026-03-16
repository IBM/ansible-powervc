#!/usr/bin/python

import requests


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
        mod.fail_json(
            msg=f"No service found with name '{service_name}'",
            changed=False,
        )
    endpoint = next((ep for ep in all_endpoints if ep.service_id == service_id), None)
    if not endpoint:
        mod.fail_json(
            msg=f"No endpoint found for '{service_name}'",
            changed=False,
        )
    return endpoint.url.replace("%(tenant_id)s", tenant_id)


def fabric_ops(
    module,
    endpoint,
    authtoken,
    tenant_id,
    verify,
    state,
    fabric_id=None,
    body=None,
):
    headers = get_headers(authtoken)
    if state == "absent":
        if not fabric_id:
            module.fail_json(msg="fabric_id is required when state=absent")
        url = f"{endpoint}/san-fabrics/{fabric_id}"
        response = requests.delete(
            url,
            headers=headers,
            verify=verify,
        )
        if response.status_code == 204:
            return dict(
                changed=True,
                msg=f"Delete operation for fabric '{fabric_id}' initiated successfully",
            )
        module.fail_json(
            msg="Failed to delete fabric",
            status_code=response.status_code,
            response=response.text,
            changed=False,
        )


    if fabric_id:
        url = f"{endpoint}/san-fabrics/{fabric_id}"
        response = requests.get(
            url,
            headers=headers,
            verify=verify,
        )
        if response.status_code != 200:
            module.fail_json(
                msg="Failed to fetch fabric",
                status_code=response.status_code,
                response=response.text,
                changed=False,
            )
        return dict(
            changed=False,
            result=response.json(),
        )


    if state == "present" and not body:
        url = f"{endpoint}/san-fabrics/detail"
        response = requests.get(
            url,
            headers=headers,
            verify=verify,
        )
        if response.status_code != 200:
            module.fail_json(
                msg="Failed to fetch fabrics",
                status_code=response.status_code,
                response=response.text,
                changed=False,
            )
        return dict(
            changed=False,
            result=response.json(),
        )


    if state == "present" and body:
        url = f"{endpoint}/san-fabrics"
        response = requests.post(
            url,
            headers=headers,
            json=body,
            verify=verify,
        )
        if response.status_code == 200:
            return dict(
                changed=True,
                msg="Fabric create operation initiated successfully",
                result=response.json(),
            )
        module.fail_json(
            msg="Failed to create fabric",
            status_code=response.status_code,
            response=response.text,
            changed=False,
        )
