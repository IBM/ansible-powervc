#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: unmanage_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs Unmanage operations on the Virtual Machine.
description:
  - This playbook helps in performing the Unmanage operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    required: true
    type: str
  id:
    description:
      - ID of the VM
    type: str

'''

EXAMPLES = '''
  - name: VM Unmanage Playbook
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
       - name: Perform VM Unmanage Operations
         ibm.powervc.unmanage_vm:
            auth: "{{ auth }}"
            name: "NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Unmanage Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Unmanage Operations
         ibm.powervc.unmanage_vm:
            cloud: "CLOUD_NAME"
            name: "NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_unmanage import unmanage_ops


class UnmanageVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
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
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            res = unmanage_ops(self, self.conn, authtoken, tenant_id, vm_id)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = UnmanageVMModule()
    module()


if __name__ == '__main__':
    main()
