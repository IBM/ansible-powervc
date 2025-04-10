#!/usr/bin/python

"""
This module performs the PowerVC Server Create/delete operations
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


def get_collocation_rules_id(mod, connectn, authtoken, tenant_id, collocation_rule_name):
    service_name = "compute"
    endpoint_compute = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    rule_url = f"{endpoint_compute}/os-server-groups"
    headers_scg = get_headers(authtoken)
    responce = requests.get(rule_url, headers=headers_scg, verify=False)
    collocation_id = None
    for server_group in responce.json()["server_groups"]:
        if server_group["name"] == collocation_rule_name:
            collocation_id = {"group": server_group["id"]}
            break
    return collocation_id


def server_flavor(mod, connectn, authtoken, tenant_id, flavor_id, image_id, volid, template_id, scg_id):
    service_name = "compute"
    endpoint_compute = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    image_url = f"{endpoint_compute}/images/{image_id}"
    headers_scg = get_headers(authtoken)
    responce = requests.get(image_url, headers=headers_scg, verify=False)
    volume_id = responce.json()['image']['metadata']['block_device_mapping'][0]['volume_id']  # to get image volume_id
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    vol_url = f"{endpoint}/volumes/{volume_id}"
    responce = requests.get(vol_url, headers=headers_scg, verify=False)
    size = responce.json()['volume']['size']
    flavor_url = f"{endpoint_compute}/flavors/{flavor_id}"
    responce = requests.get(flavor_url, headers=headers_scg, verify=False)
    # flavor_info = responce.json()
    flavor_details = {"ram": responce.json()["flavor"]["ram"], "vcpus": responce.json()["flavor"]["vcpus"], "disk": size}
    specsvmurl = f"{flavor_url}/os-extra_specs"
    responce = requests.get(specsvmurl, headers=headers_scg, verify=False)
    flavor_specs = responce.json()
    if volid:
        image_temp_id = "powervm:image_volume_type_" + volid
        flavor_specs['extra_specs'][image_temp_id] = template_id
    if scg_id:
        flavor_specs['extra_specs']['powervm:storage_connectivity_group'] = scg_id
    flavor_data = {
        **flavor_details,
        **flavor_specs  # Merge flavor_details and Include flavor_data as "extra_specs"
    }
    return flavor_data


def create_vm(headers_vm, vm_url, data, vm_name):
    """
    Performs VM Create operation
    """
    responce = requests.post(vm_url, headers=headers_vm, json=data, verify=False)
    if responce.ok:
        return (f"VM '{vm_name}' create operation is done", responce.json())
    else:
        return (f"VM '{vm_name}' create operation failed", responce.json())


def delete_vm(headers_vm, vm_url, vm_name):
    """
    Performs VM Delete operation
    """
    responce = requests.delete(vm_url, headers=headers_vm, verify=False)
    if responce.ok:
        return (f"VM '{vm_name}' has been removed/deleted")


def server_ops(mod, connectn, authtoken, tenant_id, vm_name, state, data, vm_id=None):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    headers_vm = get_headers(authtoken)
    if state == 'absent':
        if not vm_id:
            vm_id = mod.conn.compute.find_server(vm_name, ignore_missing=False).id
        vm_url = f"{endpoint}/servers/{vm_id}"
        result = delete_vm(headers_vm, vm_url, vm_name)
    elif state == 'present':
        json_string = json.dumps(data)
        input_data = json.loads(json_string.replace("'", '"'))
        filtered_data = {
            k: v
            for k, v in input_data["server"].items()
            if v is not None
        }
        json_data = {"server": filtered_data}
        vm_url = f"{endpoint}/servers"
        result = create_vm(headers_vm, vm_url, json_data, vm_name)
    return result
