#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: snapshot_vm
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Takes the Snapshot of VM's All/Boot/Specific volumes.
description:
  - This playbook helps in performing the Snapshot operations on the VM based on the inputs: volume type and volume name.
options:
  name:
    description:
      - Name of the VM
    required: true
    type: str
  volume:
    description:
      - Name of the Volume type: All/Specific/Boot
      - Provide the Volume name if volume type is Specific
    required: true
    type: dict
  snapshot_name:
    description:
      - Name of the Snapshot
    type: str
  snapshot_description:
    description:
      - Description of the Snapshot
    type: str
'''

EXAMPLES = '''
  - name: VM Specific Volume Snapshot Playbook
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
       - name:  Perform VM Snapshot Operations on Specific volumes
         ibm.powervc.snapshot_vm:
            auth: "{{ auth }}"
            vm_name: "VM_NAME"
            snapshot_name: "SNAPSHOT_NAME"
            snapshot_description: "SNAPSHOT_DESCRIPTION"
            volume:
                type: "Specific"
                name: ['VOLUME_NAME']
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM All Volume Snapshot Playbook
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
       - name:  Perform VM Snapshot Operations on All the volumes
         ibm.powervc.snapshot_vm:
            auth: "{{ auth }}"
            vm_name: "VM_NAME"
            snapshot_name: "SNAPSHOT_NAME"
            snapshot_description: "SNAPSHOT_DESCRIPTION"
            volume:
                type: "All"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Boot Volume Snapshot Playbook
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
       - name:  Perform VM Snapshot Operations on Boot volumes
         ibm.powervc.snapshot_vm:
            auth: "{{ auth }}"
            vm_name: "VM_NAME"
            snapshot_name: "SNAPSHOT_NAME"
            snapshot_description: "SNAPSHOT_DESCRIPTION"
            volume:
                type: "Boot"
            validate_certs: no
         register: result
       - debug:
            var: result

'''

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_snapshot import snapshot_ops


class SnapshotVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        volume=dict(required=True, type='dict'),
        snapshot_name=dict(required=False),
        snapshot_description=dict(required=False),
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
        snapshot_name = self.params['snapshot_name']
        snapshot_description = self.params['snapshot_description']
        volume = self.params['volume']
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
            res = snapshot_ops(self, self.conn, authtoken, tenant_id, vm_id, snapshot_name, snapshot_description, volume)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = SnapshotVMModule()
    module()


if __name__ == '__main__':
    main()
