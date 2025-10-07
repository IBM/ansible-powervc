#!/usr/bin/python

"""
This module performs the Unmanage operations on Volumes
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


def unmanage_vm(mod, endpoint, unmanage_url, authtoken, post_data):
    """
    Performs UnManage operations on the Vol provided
    """
    headers_scg = {"X-Auth-Token": authtoken, "Content-Type": "application/json"}
    responce = requests.post(unmanage_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return f"Data Volume: {post_data} Unmanage action is done"
    else:
        mod.fail_json(
            msg=f"An unexpected error occurred: {responce.json()}", changed=False
        )


def unmanage_ops(mod, connectn, authtoken, tenant_id, vol_id, host):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    unmanage_data = {"volumes": [vol_id]}
    url = f"{endpoint}/os-hosts/{host}/unmanage"
    result = unmanage_vm(mod, endpoint, url, authtoken, unmanage_data)
    return result
