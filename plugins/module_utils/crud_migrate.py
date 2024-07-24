#!/usr/bin/python

"""
This modules helps in perfoming the Migrate operations on VMs
"""

import requests
import json

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
            mod.fail_json(msg=f"No endpoint found for service '{service_name}'",changed=False)
    else:
         mod.fail_json(msg=f"No service found with the name '{service_name}'",changed=False)

def migrate_vm(mod, endpoint, vm_url, authtoken, vm_name, post_data):
    """
    Performs Post operation on the VM with the migrate data.
    """        
    headers_scg = get_headers(authtoken)
    responce = requests.post(vm_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (
            "VM Migrate is done",
            responce.json(),
        )
    else:
        module.fail_json(
            msg=f"VM Migrate Operation failed. {responce.json()}",
            changed=False,
        )

def migrate_ops(mod, connectn, authtoken, tenant_id, vm_id, vm_name, data):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    url = f"{endpoint}/servers/{vm_id}/action"
    result = migrate_vm(mod, endpoint, url, authtoken, vm_name, data)
    return result

