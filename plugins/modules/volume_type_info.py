#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: volume_type_info
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Fetches the Volume Type/Storage Templates Details
description:
  - This playbook helps in performing the Volume Type/Storage Templates Fetch operations on the Storage Name provided.
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

'''

EXAMPLES = '''
  - name: Storage Templates Details Playbook
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
       - name: Perform Volume Details Operation
         ibm.powervc.volume_type_info:
            auth: "{{ auth }}"
            name: "VOLUME_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Storage Templates Details Playbook using Volume IDs
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Details Operation
         ibm.powervc.volume_type_info:
            cloud: "CLOUD_NAME"
            id: "VOLUME_ID"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Storage Templates Details Playbook using the Volume Name
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Details Operation
         ibm.powervc.volume_type_info:
            cloud: "CLOUD_NAME"
            name: "VOLUME_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_volume_type_info import volume_ops


class VolumeTypeInfoModule(OpenStackModule):
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
        vol_type_name = self.params['name']
        vol_type_id = self.params['id']
        if vol_type_name:
            vol_type_id = self.conn.block_storage.find_type(vol_type_name, ignore_missing=False).id
        try:
            res = volume_ops(self, self.conn, authtoken, tenant_id, vol_type_id)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = VolumeTypeInfoModule()
    module()


if __name__ == '__main__':
    main()
