#!/usr/bin/python

"""
This module performs the Get Volume Details operation.
"""

import requests


def get_headers(authtoken):
    return {"X-Auth-Token": authtoken, "Content-Type": "application/json"}


def get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id):
    all_endpoints = connectn.identity.endpoints()
    services = connectn.identity.services()
    service_name_mapping = {service.id: service.type for service in services}
    service_id = next(
        (id for id, name in service_name_mapping.items() if name == service_name), None
    )
    if service_id:
        endpoint = next(
            (ep for ep in all_endpoints if ep.service_id == service_id), None
        )
        if endpoint:
            return endpoint.url.replace("%(tenant_id)s", tenant_id)
        else:
            mod.fail_json(msg=f"No endpoint found for service '{service_name}'", changed=False)
    else:
        mod.fail_json(msg=f"No service found with the name '{service_name}'", changed=False)


def get_volume_details(authtoken, volume_url):
    """
    Performs Get Volume Details operation on the Volume ID passed
    """
    headers_scg = get_headers(authtoken)
    responce = requests.get(volume_url, headers=headers_scg, verify=False)
    if responce.ok:
        return responce.json()


def volume_ops(mod, connectn, authtoken, tenant_id, vol_id):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    volume_url = f"{endpoint}/volumes/{vol_id}"
    result = get_volume_details(authtoken, volume_url)
    volume_metadata_url = f"{volume_url}/restricted-metadata"
    result_vol_metadata = get_volume_details(authtoken, volume_metadata_url)
    result.update(result_vol_metadata)
    return result
