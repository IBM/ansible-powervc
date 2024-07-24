#!/usr/bin/python

"""
This module helps in perfoming all the 
GET operation on Storage Connectivity Groups
"""

import requests
import json

def get_headers(authtoken):
    return {"X-Auth-Token": authtoken, "Content-Type": "application/json"}

def get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id):
  
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
            mod.fail_json(msg=f"No endpoint found for service '{service_name}'",changed=False)
    else:
         mod.fail_json(msg=f"No service found with the name '{service_name}'",changed=False)
        

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
            msg="Storage Connectivity Name (scg_name) is manadatory for update/delete operation",
            changed=False,
        )


def get_storage_connectivity_group_details(authtoken, endpoint):
    """
    Gets the SCG Details
    """
    headers_scg = get_headers(authtoken)
    response = requests.get(endpoint, headers=headers_scg, verify=False)
    if response.ok:
        return response.json()


def scg_ops(mod, connectn, authtoken, tenant_id, scg_name):
    """
    Performs the SCG Get Operations based on the action input
    """
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    if scg_name:
        scg_url = endpoint + "/storage-connectivity-groups" + "?deploy_ready_only=true"
        scg_id = get_storage_connectivity_group_id(mod, scg_url, authtoken, scg_name)
        endpoint = endpoint + "/storage-connectivity-groups/" + scg_id
        result = get_storage_connectivity_group_details(authtoken, endpoint)
    else:
        endpoint = endpoint + "/storage-connectivity-groups/detail?include_ports=true"
        result = get_storage_connectivity_group_details(authtoken, endpoint)
    return result        
