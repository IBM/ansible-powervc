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

def capture_vm(mod, endpoint, vm_url, authtoken, post_data, img_name):
       responce = requests.post(vm_url, headers=get_headers(authtoken), json=post_data, verify=False)
       if responce.ok:
           return (f"VM Capture Image '{img_name}' operation has been completed")
       else:
           mod.fail_json(
            msg=f"An unexpected error occurred: {responce.json()}", changed=False
        )

def capture_ops(mod, connectn, authtoken, tenant_id, vm_id, image_name):
    service_name = "compute"
    endpoint = get_endpoint_url_by_service_name(mod, connectn, service_name, tenant_id)
    capture_data = {"createImage":{"name":image_name,"metadata":{}}}
    url = f"{endpoint}/servers/{vm_id}/action"
    result = capture_vm(mod, endpoint, url, authtoken, capture_data, image_name)
    return result
