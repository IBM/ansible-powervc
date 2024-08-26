import requests
import json
import time

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

def manage_vm(mod, endpoint, vmurl, authtoken, vm_id, post_data):
       headers_scg = {"X-Auth-Token": authtoken, "Content-Type": "application/json"}
       responce = requests.get(vmurl, headers=headers_scg,  verify=False)
       #host_value = responce.json()['server']['OS-EXT-SRV-ATTR:host']
       #unmanage_url=f"{endpoint}/os-hosts/{host_value}/unmanage"
       responce = requests.post(vmurl, headers=headers_scg, json=post_data, verify=False)
       time.sleep(10)
       if responce.ok:
           return f"VM '{vm_id}' Manage action is done {responce.json()}"
       else:
           mod.fail_json(
            msg=f"An unexpected error occurred: {responce.json()}", changed=False
        )


def manage_ops(mod, connectn, authtoken, tenant_id, vm_id, host_display_name_value):
    service_name = "compute"
    headers_scg = {"X-Auth-Token": authtoken, "Content-Type": "application/json"}
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    unmanage_data = {"servers": [vm_id]}
    url = f"{endpoint}/os-hypervisors/detail?include_remote_restart_enabled=true"
#    url = "https://9.114.116.61:8774/v2.1/ef714ed8d94f46ddb4e136c72c14f918/os-hypervisors/detail?include_remote_restart_enabled=true"
    responce = requests.get(url, headers=headers_scg,  verify=False)
    #host_display_name_value = "neo50-9.47.73.8"
    data = responce.json()
# Iterate through the hypervisors to find the corresponding "hypervisor_hostname"
    result = None
    for hypervisor in data["hypervisors"]:
        if hypervisor["service"]["host_display_name"] == host_display_name_value:
            #result = hypervisor["hypervisor_hostname"]
            result = hypervisor["service"]["host"]
            break

    #print(result)
    #url = "https://9.114.116.61:8774/v2.1/ef714ed8d94f46ddb4e136c72c14f918/os-hosts/824721L_215441A/onboard"
    url = f"{endpoint}/os-hosts/{result}/onboard"
    #manage_data = '{"synchronous":false,"servers":["050960ea-753a-488b-87da-b8516fd78faf"],"preparation":{"servers":[],"network_vswitch":"","move_network_components":false}}'
    manage_data = {"synchronous":"false","servers":[vm_id],"preparation":{"servers":[],"network_vswitch":"","move_network_components":"false"}}
    result = manage_vm(mod, endpoint, url, authtoken, vm_id, manage_data)
    return result

