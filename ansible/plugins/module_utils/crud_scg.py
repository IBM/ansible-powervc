#!/usr/bin/python

"""
This module helps in perfoming the 
Create, Update and Delete operations on Storage Connectivity Groups
"""

import requests
import json

def get_headers(authtoken):
    return {"X-Auth-Token": authtoken, "Content-Type": "application/json"}

def get_endpoint_url_by_service_name(connectn, service_name, tenant_id):
  
    """
    Get the endpoint url for that particular Service
    
    """
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
            return f"No endpoint found for service '{service_name}'"
    else:
        return f"No service found with the name '{service_name}'"


def get_storage_connectivity_group_id(mod, scg_url, authtoken, desired_display_name):
    """
    Gets the Storage Connectivity Group ID
    This SCG ID will be used in further Update/Delete operations
    """
    headers_scg = get_headers(authtoken)
    if desired_display_name:
        responce = requests.get(scg_url, headers=headers_scg, verify=False)
        scgs = responce.json()
        found_entry = None
        for entry in scgs["storage_connectivity_groups"]:
            if entry["display_name"] == desired_display_name:
                found_entry = entry
                break
        # If the entry is found, extract the "id"
        if found_entry:
            desired_id = found_entry["id"]
            return found_entry["id"]
        else:
            mod.fail_json(
                msg=f"No entry found with display name '{desired_display_name}'",
                changed=False,
            )
    else:
        mod.fail_json(
            msg="Storage Connectivity Name (name) is manadatory for update/delete operation",
            changed=False,
        )


def get_storage_connectivity_groups(authtoken, endpoint):
    """
    Gets the SCG Details
    """
    headers_scg = get_headers(authtoken)
    endpoint = endpoint + "/storage-connectivity-groups/detail?include_ports=true"
    response = requests.get(endpoint, headers=headers_scg, verify=False)
    scgs = response.json()
    return scgs


def delete_storage_connectivity_groups(mod, scg_url, authtoken, scg_name):
    """
    Deletes the SCG
    """
    headers_scg = get_headers(authtoken)
    responce = requests.delete(scg_url, headers=headers_scg, verify=False)
    if responce.ok:
        return "Deleted the provided Storage Connectivity group"
    else:
        mod.fail_json(
            msg=f"An unexpected error occurred: {responce.json()}", changed=False
        )

def put_storage_connectivity_groups(mod, scg_url, authtoken, put_data, scg_name):
    """
    For Updating the SCG based on the input details
    """
    headers_scg = get_headers(authtoken)
    responce = requests.put(scg_url, headers=headers_scg, json=put_data, verify=False)
    if responce.ok:
        return "Updated the Storage Connectivity group with", put_data
    else:
        mod.fail_json(
            msg=f"An unexpected error occurred: {responce.json()}", changed=False
        )


def post_storage_connectivity_groups(module, scg_url, authtoken, post_data):
    """
    Creates the SCG based on the user input details
    """
    input_data_options = [
        "display_name",
        "data_connectivity",
        "boot_connectivity",
        "auto_add_vios",
        "exact_redundancy",
        "enabled",
        "fabric_set_npiv",
        "fabric_set_req",
        "fc_storage_access",
        "include_untagged",
        "port_tag",
        "ports_per_fabric_npiv",
        "vios_ids",
        "vios_redundancy",
    ]
    headers_scg = get_headers(authtoken)
    responce = requests.post(scg_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (
            "Created the Storage Connectivity group",
            post_data["storage_connectivity_group"]["display_name"],
            responce.json(),
        )
    else:
        module.fail_json(
            msg=f"Paramters required for creating the SCG are {input_data_options}. {responce.json()}",
            changed=False,
        )

def scg_ops(mod, connectn, authtoken, state, action, tenant_id, scg_name, scg_id, data):
    """
    Performs the SCG CRUD Operations based on the action input
    """
    service_name = "compute"
    json_string = json.dumps(data)
    input_data = json.loads(json_string.replace("'", '"'))
    filtered_data = {
        k: v
        for k, v in input_data["storage_connectivity_group"].items()
        if v is not None
    }
    json_data = {"storage_connectivity_group": filtered_data}
    endpoint = get_endpoint_url_by_service_name(connectn, service_name, tenant_id)
    if state in ["get", "list", "fetch"]:
        result = get_storage_connectivity_groups(authtoken, endpoint)
    elif state == 'absent':
        scg_get_url = (
            endpoint + "/storage-connectivity-groups" + "?deploy_ready_only=true"
        )
        if not scg_id:
            scg_id = get_storage_connectivity_group_id(
                mod, scg_get_url, authtoken, scg_name
            )
        scg_put_url = endpoint + "/storage-connectivity-groups/" + scg_id
        result = delete_storage_connectivity_groups(
            mod, scg_put_url, authtoken, scg_name
        )
    elif state == 'present' and (scg_name or scg_id):
        scg_get_url = (
            endpoint + "/storage-connectivity-groups" + "?deploy_ready_only=true"
        )
        if not scg_id:
            scg_id = get_storage_connectivity_group_id(
                mod, scg_get_url, authtoken, scg_name
            )
        scg_put_url = endpoint + "/storage-connectivity-groups/" + scg_id
        result = put_storage_connectivity_groups(
            mod, scg_put_url, authtoken, json_data, scg_name
        )
    elif state == 'present' and not scg_name:
        scg_post_url = endpoint + "/storage-connectivity-groups"
        result = post_storage_connectivity_groups(
            mod, scg_post_url, authtoken, json_data
        )
    else:
        mod.fail_json(
            msg="For deleting the SCG: Pass state as 'absent' with name as the required Storage Connectivity group. Similarly pass stes as 'present' for creating/updating the SCG.",
            changed=False,
        )
    return result        
