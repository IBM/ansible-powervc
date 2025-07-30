#!/usr/bin/python

"""
This module performs the Get Snapshot Details operation.
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


def get_snapshot_details(authtoken, snapshot_url):
    """
    Performs Get Snapshot Details operation on the Snapshot ID passed
    """
    headers_scg = get_headers(authtoken)
    responce = requests.get(snapshot_url, headers=headers_scg, verify=False)
    if responce.ok:
        return responce.json()


def snapshot_ops(mod, connectn, authtoken, tenant_id, snapshot_id):
    service_name = "volume"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    if snapshot_id:
        snapshot_url = f"{endpoint}/snapshots/{snapshot_id}"
        result = get_snapshot_details(authtoken, snapshot_url)
    else:
        snapshot_url = f"{endpoint}/snapshots"
        result = get_snapshot_details(authtoken, snapshot_url)
    return result
