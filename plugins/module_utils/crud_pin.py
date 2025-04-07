#!/usr/bin/python

"""
This module performs the Pin operations (soft, hard, no_pin) on VMs.
"""

import requests
# import json


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


def pin_vm(mod, endpoint, vmurl, authtoken, post_data):
    """
    Performs Post operation on the VM with the pin details.
    """
    headers_scg = {"X-Auth-Token": authtoken, "Content-Type": "application/json"}
    responce = requests.get(vmurl, headers=headers_scg, verify=False)
    host_value = responce.json()['server']['OS-EXT-SRV-ATTR:host']
    post_data["metadata"]["original_host"] = host_value
    pin_url = f"{vmurl}/metadata"
    responce = requests.post(pin_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (f"VM Pin action is done", responce.json())


def pin_ops(mod, connectn, authtoken, tenant_id, vm_id, pin_type):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    url = f"{endpoint}/servers/{vm_id}"
    if pin_type == "softpin":
        pin_data = {"metadata": {"pin_vm": "true", "move_pin_vm": "true"}}
    elif pin_type == "hardpin":
        pin_data = {"metadata": {"pin_vm": "true", "move_pin_vm": "false"}}
    elif pin_type == "nopin":
        pin_data = {"metadata": {"pin_vm": "false", "move_pin_vm": "true"}}
    else:
        mod.fail_json(msg="Allowed values for pin_type are softpin, hardpin and nopin", changed=False)
    result = pin_vm(mod, endpoint, url, authtoken, pin_data)
    return result
