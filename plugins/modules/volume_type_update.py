#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: volume_type_update
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Performs the Volume Type Update Operations
description:
  - This playbook helps in performing the Volume Update operations on the Volume provided.
options:
  name:
    description:
      - Name of the Volume Type
    required: true
    type: str
  id:
    description:
      - ID of the Volume Type
    type: str
  extra_specs:
    description:
      - extra specifications of the volume type
    type: dict

'''

EXAMPLES = '''
  - name: Volume Type Details Playbook
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
         ibm.powervc.volume_type_update:
            auth: "{{ auth }}"
            name: "VOLUME_NAME"
            extra_specs:
                    drivers:flashcopy_rate: "50"
                    drivers:grainsize: "256"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Type Details Playbook using Volume Name
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Details Operation
         ibm.powervc.volume_type_update:
            cloud: "CLOUD_NAME"
            id: "VOLUME_ID"
            extra_specs:
                    drivers:flashcopy_rate: "50"
                    drivers:grainsize: "256"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Type Details Playbook using the Volume IDs
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Volume Details Operation
         ibm.powervc.volume_update:
            cloud: "CLOUD_NAME"
            name: "VOLUME_NAME"
            extra_specs:
                    "drivers:provision_type":"thin"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_volume_type_update import volume_ops


class VolumeTypeUpdateModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        extra_specs=dict(type='dict'),
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
        extra_specs = self.params['extra_specs']
        if vol_name:
            vol_id = self.conn.block_storage.find_volume(vol_name, ignore_missing=False).id

        try:
            res = volume_ops(self, self.conn, authtoken, tenant_id, vol_id, extra_specs)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = VolumeUpdateModule()
    module()


if __name__ == '__main__':
    main()
