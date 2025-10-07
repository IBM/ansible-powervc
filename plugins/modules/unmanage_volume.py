#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: unmanage_vol
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs Unmanage operations on the Volumes.
description:
  - This playbook helps in performing the Unmanage operations on the Volume provided.
options:
  name:
    description:
      - Name of the Volume
    required: true
    type: str
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
  - name: Volume Unmanage Playbook
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
       - name: Perform Volume Unmanage Operations
         ibm.powervc.unmanage_vol:
            auth: "{{ auth }}"
            name: "NAME"
            host_metadata_name: "HOST_METADATA_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Unmanage Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Unmanage Operations
         ibm.powervc.unmanage_vol:
            cloud: "CLOUD_NAME"
            id: "ID"
            host_metadata_name: "HOST_METADATA_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_unmanage_vol import unmanage_ops


class UnmanageVolModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        host_name=dict(required=True),
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
        vol_name = self.params['name']
        vol_id = self.params['id']
        host = self.params['host_name']
        if vol_name:
            vol_id = self.conn.block_storage.find_volume(vol_name, ignore_missing=False).id
        try:
            res = unmanage_ops(self, self.conn, authtoken, tenant_id, vol_id, host)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = UnmanageVolModule()
    module()


if __name__ == '__main__':
    main()
