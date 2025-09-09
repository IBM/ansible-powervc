#!/usr/bin/python

"""
This module helps in perfoming the Copy Volume Type operations
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


def copy_voltype(module, authtoken, voltype_url, id, name):
    headers_scg = get_headers(authtoken)
    voltypeid_url = f"{voltype_url}/{id}"
    responce = requests.get(voltypeid_url, headers=headers_scg, verify=False)
    data = responce.json()
    data["volume_type"].pop("id", None)
    data["volume_type"]["name"] = name
    data["volume_type"]["extra_specs"]["drivers:display_name"] = name
    data["volume_type"].pop("is_public", None)
    responce = requests.post(voltype_url, headers=headers_scg, json=data, verify=False)
    if responce.ok:
        return responce.json()


def copy_voltype_ops(mod, connectn, authtoken, tenant_id, voltemp_id, name):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    voltype_url = f"{endpoint}/types"
    result = copy_voltype(mod, authtoken, voltype_url, voltemp_id, name)
    return result
