#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: pin_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs the Pin VM operations.
description:
  - This playbook helps in performing the Pin operations on the VM provided.
options:
  name:
    description:
      - Name of the Server
    type: str
  id:
    description:
      - ID of the VM
    type: str
  pin_type:
    description:
      - Pin Type - Allowed values are no_pin, soft_pin, hard_pin
    type: str

'''

EXAMPLES = '''
  - name: Perform Soft Pin Operations on the VM
    hosts: all
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
       - name: Pin VM Task
         ibm.powervc.pin_vm:
            auth: "{{ auth }}"
            name: "NAME"
            pin_type: "PIN_TYPE"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_pin import pin_ops


class PinOpsModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        pin_type=dict(required=True),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        vm_name = self.params['name']
        vm_id = self.params['id']
        pin_type = self.params['pin_type']
        tenant_id = self.conn.session.get_project_id()
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            res = pin_ops(self, self.conn, authtoken, tenant_id, vm_id, pin_type)
            self.exit_json(changed=False, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = PinOpsModule()
    module()


if __name__ == '__main__':
    main()
