#!/usr/bin/python

"""
This module performs the PowerVC Volume Type Update operations
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


def post_volume_type(headers_vm, url, extra_specs):
    """
    Performs Update Volume Type operation
    """
    data = {'extra_specs': extra_specs}
    responce = requests.post(url, headers=headers_vm, json=data, verify=False)
    if responce.ok:
        return (f"Volume Type changes are done - {responce.json()}")


def volume_ops(mod, connectn, authtoken, tenant_id, vol_type_id, extra_specs):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    headers_vm = get_headers(authtoken)
    volume_type_url = f"{endpoint}/types/{vol_type_id}/extra_specs"
    result = post_volume_type(mod, headers_vm, volume_type_url, extra_specs)
    return result
