#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: resize_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Resizes the VM based on the compute templates parameter.
description:
  - This playbook helps in performing the Resize operations on the VM based on the compute templates parameter.
options:
  name:
    description:
      - Name of the VM
    type: str
  id:
    description:
      - ID of the VM
    type: str  
  template_type:
    description:
      - Name of the Compute Template
    required: true
    type: str

'''

EXAMPLES = '''
  - name: VM Resize Playbook
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
       - name: Performing the DELETE SCG Operation
         ibm.powervc.resize_vm:
            auth: "{{ auth }}"
            vm_name: "VM_NAME"
            template_type: "TEMPLATE_TYPE"
            validate_certs: no
         register: result
       - debug:
            var: result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_resize import resize_ops


class ResizeVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        template_type=dict(required=True),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vm_name = self.params['name']
        vm_id = self.params['id']        
        template_type = self.params['template_type']
        template_id = self.conn.compute.find_flavor(template_type, ignore_missing=False).id
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id        
        try:
            res = resize_ops(self, self.conn, authtoken, tenant_id, vm_id, template_id, vm_name)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = ResizeVMModule()
    module()


if __name__ == '__main__':
    main()
