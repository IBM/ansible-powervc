#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: manage_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs the Manage operations on the Virtual Machine.
description:
  - This playbook helps in performing the Manage operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    type: str
  id:
    description:
      - ID of the VM
    type: str
  host:
    description:
      - ID of the Host
    type: str

'''

EXAMPLES = '''
  - name: VM Manage Playbook
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
       - name: Perform VM Manage Operations
         ibm.powervc.manage_vm:
            auth: "{{ auth }}"
            id: "VM_ID"
            host: "HOST_ID"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_manage import manage_ops


class ManageVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        host=dict(required=True),
    )
    module_kwargs = dict(
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'id'],
        ]
    )

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vm_name = self.params['name']
        vm_id = self.params['id']
        host = self.params['host']
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            res = manage_ops(self, self.conn, authtoken, tenant_id, vm_id, host)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = ManageVMModule()
    module()


if __name__ == '__main__':
    main()
