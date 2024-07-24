#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'requirements': ['python >= 3.9','ansible >= openstack.cloud'],
                    'status': ['testing'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: migrate_vm
short_description: For Migrating the VM.
description:
  - This playbook helps in performing the Migrate operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    type: str
  host:
    description:
      - Name of the Host
    type: str
'''

EXAMPLES = '''
---
  - name: VM Migrate Playbook
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
       - name: Perform VM Migrate Operations
         ibm.powervc.migate_vm:
            auth: "{{ auth }}"
            name: "NAME"
	    host: "HOST"
            validate_certs: no
         register: result
       - debug:
            var: result

'''

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.powervc.cloud.plugins.module_utils.crud_migrate import migrate_ops

class MigrateVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(required=True),
        host=dict(required=False),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vm_name = self.params['name']
        host = self.params['host']
        vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        try:
                data = {"os-migrateLive":{"host":host,"block_migration":"false","disk_over_commit":"true"}}
                res = migrate_ops(self, self.conn, authtoken, tenant_id, vm_id, vm_name, data)
                self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = MigrateVMModule()
    module()


if __name__ == '__main__':
    main()

