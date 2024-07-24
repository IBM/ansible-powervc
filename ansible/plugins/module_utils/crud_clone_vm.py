#!/usr/bin/python

"""
This module helps in perfoming the Clone operations on VMs
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


def clone_vm(module, clonevm_url, authtoken, post_data):
    """
    Performs Post operation on the VM with the clone data.
    """    
    input_data_options = [
        "clonevm_name",
        "network_name",
    ]
    headers_scg = get_headers(authtoken)
    responce = requests.post(clonevm_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (
            "VM has been cloned with the below details",
            post_data,
            responce.json(),
        )
    else:
        module.fail_json(
            msg=f"Paramters required for Cloning the VM are {input_data_options}",
            changed=False,
        )

def clone_vm_ops(mod, connectn, authtoken, tenant_id, vm_id, data):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    clonevm_url = f"{endpoint}/servers/{vm_id}/action"
    result = clone_vm(mod, clonevm_url, authtoken, data)
    return result

