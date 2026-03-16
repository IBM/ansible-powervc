#!/usr/bin/python
# -*- coding: utf-8 -*-

DOCUMENTATION = r'''
---
module: fabric
short_description: Manage SAN fabrics in PowerVC

description:
  - Register, delete, or retrieve SAN fabrics in PowerVC.

options:
  state:
    description:
      - Desired state of the fabric.
    type: str
    choices: [present, absent]
    default: present

  fabric_id:
    description:
      - ID of the SAN fabric.
    type: str

  access_ip:
    description:
      - Management IP of the SAN switch.
    type: str

  user_id:
    description:
      - Username for the SAN switch.
    type: str

  password:
    description:
      - Password for the SAN switch.
    type: str
    no_log: true

  fabric_display_name:
    description:
      - Display name of the fabric.
    type: str

  fabric_type:
    description:
      - Type of fabric.
    type: str

  zoning_policy:
    description:
      - Zoning policy.
    type: str

  auto_add_host_key:
    description:
      - Automatically add host key.
    type: bool
    default: true

author:
  - IBM PowerVC Team
'''

EXAMPLES = r'''
# Get all fabrics
- name: Get fabrics
  ibm.powervc.fabric:
    cloud: powervc

# Get specific fabric
- name: Get fabric
  ibm.powervc.fabric:
    cloud: powervc
    fabric_id: fab123

# Register fabric
- name: Register fabric
  ibm.powervc.fabric:
    cloud: powervc
    state: present
    access_ip: 9.2.4.6
    user_id: admin
    password: password
    fabric_display_name: Fabric1
    fabric_type: brocade
    zoning_policy: initiator

# Delete fabric
- name: Delete fabric
  ibm.powervc.fabric:
    cloud: powervc
    state: absent
    fabric_id: fab123
'''


from ansible_collections.ibm.powervc.plugins.module_utils.crud_fabric import (
    fabric_ops,
    get_endpoint_url_by_service_name,
)

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
    OpenStackModule,
)


class FabricModule(OpenStackModule):
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        fabric_id=dict(type="str"),
        access_ip=dict(type="str"),
        user_id=dict(type="str"),
        password=dict(type="str", no_log=True),
        fabric_display_name=dict(type="str"),
        fabric_type=dict(type="str"),
        zoning_policy=dict(type="str"),
        auto_add_host_key=dict(type="bool", default=True),
        virtual_fabric_id=dict(type="str"),
        port=dict(type="int"),
        vsan=dict(type="str"),
    )
    module_kwargs = dict(supports_check_mode=True)


    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        verify = self.conn.session.verify
        state = self.params.get("state")
        fabric_id = self.params.get("fabric_id")
        access_ip = self.params.get("access_ip")
        user_id = self.params.get("user_id")
        password = self.params.get("password")
        fabric_display_name = self.params.get("fabric_display_name")
        fabric_type = self.params.get("fabric_type")
        zoning_policy = self.params.get("zoning_policy")
        auto_add_host_key = self.params.get("auto_add_host_key")
        virtual_fabric_id = self.params.get("virtual_fabric_id")
        port = self.params.get("port")
        vsan = self.params.get("vsan")
        endpoint = get_endpoint_url_by_service_name(
            self, self.conn, "volume", tenant_id
        )
        body = None
        if state == "present":
            registration = {
                "access_ip": access_ip,
                "user_id": user_id,
                "password": password,
                "fabric_display_name": fabric_display_name,
                "fabric_type": fabric_type,
                "zoning_policy": zoning_policy,
                "auto_add_host_key": auto_add_host_key,
            }
            if fabric_type == "brocade":
                registration["virtual_fabric_id"] = virtual_fabric_id
            if fabric_type == "cisco":
                registration["port"] = port
                registration["vsan"] = vsan
            body = {
                "fabric": {
                    "registration": registration
                }
            }
        result = fabric_ops(
            module=self,
            endpoint=endpoint,
            authtoken=authtoken,
            tenant_id=tenant_id,
            verify=verify,
            state=state,
            fabric_id=fabric_id,
            body=body,
        )
        self.exit_json(**result)


def main():
    module = FabricModule()
    module()


if __name__ == "__main__":
    main()
