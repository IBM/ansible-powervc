#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: manage_vol
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs Manage operations on the Volumes.
description:
  - This playbook helps in performing the Manage operations on the Volume provided.
options:
  id:
    description:
      - ID of the Volume
    type: str
  host_metadata_name:
    description:
      - Name of the Host from Storage specific metadata
    type: str

'''

EXAMPLES = '''
  - name: Volume Manage Playbook
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
       - name: Perform Volume Manage Operations
         ibm.powervc.manage_vol:
            auth: "{{ auth }}"
            id: "ID"
            host_metadata_name: "HOST_METADATA_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Manage Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Manage Operations
         ibm.powervc.manage_vol:
            cloud: "CLOUD_NAME"
            id: "ID"
            host_metadata_name: "HOST_METADATA_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_manage_vol import manage_ops


class ManageVolModule(OpenStackModule):
    argument_spec = dict(
        id=dict(),
        host_metadata_name=dict(required=True),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vol_id = self.params['id']
        host = self.params['host_metadata_name']
        try:
            res = manage_ops(self, self.conn, authtoken, tenant_id, vol_id, host)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = ManageVolModule()
    module()


if __name__ == '__main__':
    main()
