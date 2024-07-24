#!/usr/bin/python

"""
This module performs the Snapshot operations on VMs
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

def snapshot_vm(module, snapshotvm_url, authtoken, post_data):
    """
    Performs Snapshot VM operation on the volume_list passed.
    """      
    input_data_options = [
        "snapshot_name",
        "description",
        "volumes",
    ]
    headers_scg = get_headers(authtoken)
    responce = requests.post(snapshotvm_url, headers=headers_scg, json=post_data, verify=False)
    if responce.ok:
        return (
            "VM Snapshot is done",
            post_data["vm-snapshot"],
            responce.json(),
        )
    else:
        module.fail_json(
            msg=f"Paramters required for VM Snapshot are {input_data_options}. {responce.json()}",
            changed=False,
        )

def get_volumeids_bytype(mod, connectn, endpoint, authtoken, tenant_id, vm_id, volume_type):
    """
    Gets the Volume Ids (Boot/Data/Specific) in the form of list
    """    
    headers_scg = get_headers(authtoken)
    volume_url = f"{endpoint}/servers/{vm_id}"
    responce = requests.get(volume_url, headers=headers_scg, verify=False)
    volume_details = responce.json()
    volume_ids = [volume['id'] for volume in volume_details['server']['os-extended-volumes:volumes_attached']]
    boot_vol = []
    data_vol = []
    for i in volume_ids:
        service_name = "volume"
        endpoint = get_endpoint_url_by_service_name(connectn, service_name, tenant_id)
        vol_url = f"{endpoint}/volumes/{i}"
        responce = requests.get(vol_url, headers=headers_scg, verify=False)
        vol_details = responce.json()
        volume_info = vol_details.get("volume", {})
        boot_volume = volume_info["metadata"].get("is_boot_volume", "False")
        volume_id = vol_details["volume"]["id"]
        if boot_volume.lower() == "true":
            boot_vol.append(volume_id)
        else:
            data_vol.append(volume_id)
    return data_vol if volume_type == "Data" else (boot_vol if volume_type == "Boot" else volume_ids)

def get_volumeids_byname(mod, connectn, endpoint, authtoken, tenant_id, volume_name):
    vol_id = []
    for name in volume_name:
        vol_id.append(connectn.block_storage.find_volume(name, ignore_missing=False).id)
    return vol_id

def snapshot_ops(mod, connectn, authtoken, tenant_id, vm_id, snapshot_name, snapshot_description, volume):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    if volume["name"] and volume["type"] == "Specific":
        volume_list = get_volumeids_byname(mod, connectn, endpoint, authtoken, tenant_id,  volume["name"])
    elif volume["type"] in ["All","Boot"]:
        volume_list = get_volumeids_bytype(mod, connectn, endpoint, authtoken, tenant_id, vm_id, volume["type"])
    else:
         mod.fail_json(
                 msg=f"Pass Volume details as type: All or Boot or Specific, Pass Volume name only if type is specific",
            changed=False,
        )        
    post_data = {"vm-snapshot":{"name":snapshot_name,"description":snapshot_description,"volumes":volume_list}}
    snapshotvm_url = f"{endpoint}/servers/{vm_id}/action"
    result = snapshot_vm(mod, snapshotvm_url, authtoken, post_data)
    return result

