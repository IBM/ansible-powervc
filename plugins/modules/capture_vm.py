#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: capture_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Capturing the Image out of the Virtual Machine.
description:
  - This playbook helps in performing the Image Create/Capture operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    type: str
  id:
    description:
      - ID of the VM
    type: str
  image_name:
    description:
      - Name of the Captured Image
    required: true
    type: str

'''

EXAMPLES = '''
---
  - name: VM Capture Playbook
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
       - name: Perform VM Capture Operations
         ibm.powervc.capture_vm:
            auth: "{{ auth }}"
            name: "NAME"
            image_name: "IMAGE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Capture Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Capture Operations
         ibm.powervc.capture_vm:
            cloud: "CLOUDNAME"
            name: "NAME"
            image_name: "IMAGE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Capture Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Capture Operations
         ibm.powervc.capture_vm:
            cloud: "CLOUDNAME"
            id: "VM_ID"
            image_name: "IMAGE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_capture_vm import capture_ops


class CaptureVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        image_name=dict(required=True),
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
        image_name = self.params['image_name']
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            res = capture_ops(self, self.conn, authtoken, tenant_id, vm_id, image_name)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = CaptureVMModule()
    module()


if __name__ == '__main__':
    main()
