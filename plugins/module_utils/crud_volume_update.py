#!/usr/bin/python

"""
This module performs the PowerVC Volume Update operations
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


def post_volume(headers_vm, vm_url, size):
    """
    Performs Post Volume operation
    """
    data = {"ibm-extend": {"new_size": size}}
    responce = requests.post(vm_url, headers=headers_vm, json=data, verify=False)
    if responce.ok:
        return (f"Volume Data Size changes to {size}")


def put_volume(headers_vm, vm_url, enable_sharing_vm):
    """
    Performs Update Volume operation
    """
    if enable_sharing_vm:
        data = {"volume": {"multiattach": True}}
    else:
        data = {"volume": {"multiattach": False}}
    responce = requests.put(vm_url, headers=headers_vm, json=data, verify=False)
    if responce.ok:
       return responce.json()


def volume_ops(mod, connectn, authtoken, tenant_id, vol_id, size, enable_sharing_vm):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    headers_vm = get_headers(authtoken)
    volume_url = f"{endpoint}/volumes/{vol_id}"
    vol_post_url = f"{volume_url}/action"
    if size is not None and enable_sharing_vm is None:
        result = post_volume(headers_vm, vol_post_url, size)
    if size is None and enable_sharing_vm is not None:
        result = put_volume(headers_vm, volume_url, enable_sharing_vm)
    elif size is not None and enable_sharing_vm is not None:
        result = post_volume(headers_vm, vol_post_url, size)
        result_update = put_volume(headers_vm, volume_url, enable_sharing_vm)
        result = "Volume Updates are done", result_update
    return result
