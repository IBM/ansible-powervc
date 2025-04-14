#!/usr/bin/python

"""
This module performs the Resize operations on VM.
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
            mod.fail_json(msg=f"No endpoint found for service '{service_name}'", changed=False)
    else:
        mod.fail_json(msg=f"No service found with the name '{service_name}'", changed=False)


def resize_vm(mod, resize_url, authtoken, post_data, vm_name):
    headers_scg = get_headers(authtoken)
    responce = requests.post(resize_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (
            "VM Resize action is done",
        )
    else:
        mod.fail_json(
            msg=f"Resize operation failed. {responce.json()}",
            changed=False,
        )


def get_flavor_details(mod, connectn, endpoint, authtoken, tenant_id, vm_id, template_id):
    """
    Gets required flavor details for the resize operation.
    """
    vm_url = f"{endpoint}/servers/{vm_id}"
    headers_scg = get_headers(authtoken)
    responce = requests.get(vm_url, headers=headers_scg, verify=False)
    response_dict = json.loads(responce.text)
    output_data1 = {"disk": response_dict["server"]["root_gb"]}
    flavor_url = f"{endpoint}/flavors/{template_id}"
    # flavorurl = endpoint + "/flavors" + "/" + template_id
    responce = requests.get(flavor_url, headers=headers_scg, verify=False)
    response_dict = json.loads(responce.text)
    output_data2 = {"ram": response_dict["flavor"]["ram"], "vcpus": response_dict["flavor"]["vcpus"]}
    flavorspecs_url = f"{flavor_url}/os-extra_specs"
    # flavorspecsurl = flavorurl + "/" + "os-extra_specs"
    responce = requests.get(flavorspecs_url, headers=headers_scg, verify=False)
    output_data3 = json.loads(responce.text)
    output_data4 = {"resize": {"flavor": {**output_data1, **output_data2, **output_data3}}}
    return output_data4


def resize_ops(mod, connectn, authtoken, tenant_id, vm_id, template_id, vm_name):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    flavor_details = get_flavor_details(mod, connectn, endpoint, authtoken, tenant_id, vm_id, template_id)
    resize_url = f"{endpoint}/servers/{vm_id}/action"
    result = resize_vm(mod, resize_url, authtoken, flavor_details, vm_name)
    return result
