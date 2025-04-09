#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: clone_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Takes Clone of the Virtual Machine.
description:
  - This playbook helps in performing the Clone operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    type: str
  id:
    description:
      - ID of the VM
    type: str
  clonevm_name:
    description:
      - Name of the Cloned VM
    required: true
    type: str
  nics:
    description:
      - A list of networks to which the instance's interface should be attached.
    required: true
    type: list

'''

EXAMPLES = '''

- name: VM Clone Playbook with Network
    hosts: localhost
    gather_facts: no
    vars:
     auth:
      auth_url: https://<POWERVC>:5000/v3
      project_name: PROJECT-NAME
      username: USERID
      password: PASSWORD
      project_domain_name: PROJECT_DOMAIN_NAME
      user_domain_name: USER_DOMAIN_NAME
    tasks:
       - name:  Perform VM Clone Operation on VM with network
         ibm.powervc.clone_vm:
            auth: "{{ auth }}"
            name: "VM_NAME"
            clonevm_name: "CLONEVM_NAME"
            nics:
                - net-name: "NET-NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Clone Playbook with Network and providing a fixed_ip
    hosts: localhost
    gather_facts: no
    vars:
     auth:
      auth_url: https://<POWERVC>:5000/v3
      project_name: PROJECT-NAME
      username: USERID
      password: PASSWORD
      project_domain_name: PROJECT_DOMAIN_NAME
      user_domain_name: USER_DOMAIN_NAME
    tasks:
       - name:  Perform VM Clone Operation on VM with network and IP details
         ibm.powervc.clone_vm:
            auth: "{{ auth }}"
            vm_name: "VM_NAME"
            clonevm_name: "CLONEVM_NAME"
            nics:
                - net-name: "NET-NAME"
                  fixed_ip: "FIXED_IP"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Clone Playbook with Network and providing a fixed_ip
    hosts: localhost
    gather_facts: no
    tasks:
       - name:  Perform VM Clone Operation on VM with network and IP details
         ibm.powervc.clone_vm:
            cloud: "CLOUD_NAME"
            name: "VM_NAME"
            clonevm_name: "CLONEVM_NAME"
            nics:
                - net-name: "NET-NAME"
                  fixed_ip: "FIXED_IP"
            validate_certs: no
         register: result
       - debug:
            var: result

'''

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_clone_vm import clone_vm_ops
import copy


class CloneVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        clonevm_name=dict(required=True),
        network=dict(),
        nics=dict(default=[], type='list', elements='raw'),
    )
    module_kwargs = dict(
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'id'],
        ]
    )

    def _parse_nics(self):
        nics = []
        stringified_nets = self.params['nics']

        if not isinstance(stringified_nets, list):
            self.fail_json(msg="The 'nics' parameter must be a list.")

        nets = [(dict((nested_net.split('='),))
                for nested_net in net.split(','))
                if isinstance(net, str) else net
                for net in stringified_nets]

        for net in nets:
            if not isinstance(net, dict):
                self.fail_json(
                    msg="Each entry in the 'nics' parameter must be a dict.")
            if net.get('net-id'):
                nics.append(net)
            elif net.get('net-name'):
                network_id = self.conn.network.find_network(
                    net['net-name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['net-name']
                net['uuid'] = network_id
                nics.append(net)
            elif net.get('fixed_ip'):
                nics.append(net)
            elif net.get('port-id'):
                nics.append(net)
            elif net.get('port-name'):
                port_id = self.conn.network.find_port(
                    net['port-name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['port-name']
                net['port-id'] = port_id
                nics.append(net)

            if 'tag' in net:
                nics[-1]['tag'] = net['tag']
        return nics

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vm_name = self.params['name']
        vm_id = self.params['id']
        clonevm_name = self.params['clonevm_name']
        nics = self._parse_nics()
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            data = {"clone-vm": {"server": {"name": clonevm_name, "networks": nics, "availability_zone": "Default Group"}}}
            res = clone_vm_ops(self, self.conn, authtoken, tenant_id, vm_id, data)
            self.exit_json(changed=False, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = CloneVMModule()
    module()


if __name__ == '__main__':
    main()
