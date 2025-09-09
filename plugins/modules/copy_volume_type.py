#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: copy_volume_type
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Takes Copy of the Volume Types/Storage Template.
description:
  - This playbook helps in performing the Copy operations on the Volume Type provided.
options:
  name:
    description:
      - Name of the Volume Type/Storage Template
    type: str
  id:
    description:
      - ID of the Volume Type/Storage Template
    type: str
  copy_voltype_name:
    description:
      - Name of the Copy Volume Type/Storage Template
    required: true
    type: str

'''

EXAMPLES = '''
- name: Volume Type Copy Playbook
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
       - name:  Perform VM Clone Operation on VM with network
         ibm.powervc.copy_volume_type:
            auth: "{{ auth }}"
            name: "VOL_TYPE_NAME"
            copy_voltype_name: "COPY_VOLTYPE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Type Copy Playbook
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
       - name:  Perform VM Clone Operation on VM with network and IP details
         ibm.powervc.copy_volume_type:
            auth: "{{ auth }}"
            vm_name: "VOL_TYPE_NAME"
            copy_voltype_name: "COPY_VOLTYPE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Volume Type Copy Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name:  Perform VM Clone Operation on VM with network and IP details
         ibm.powervc.copy_volume_type:
            cloud: "CLOUD_NAME"
            id: "VOL_TYPE_ID"
            copy_voltype_name: "COPY_VOLTYPE_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

'''

from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_copy_vol_type import copy_voltype_ops


class CopyVolumeTypeModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        copy_voltype_name=dict(required=True),
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
        copy_voltype_name = self.params['copy_voltype_name']
        if vol_type_name:
            vol_type_id = self.conn.block_storage.find_type(vol_type_name, ignore_missing=False).id
        try:
            res = copy_voltype_ops(self, self.conn, authtoken, tenant_id, vol_type_id, copy_voltype_name)
            self.exit_json(changed=False, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = CopyVolumeTypeModule()
    module()


if __name__ == '__main__':
    main()
