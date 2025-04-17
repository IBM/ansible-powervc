#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: volume_detach
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Detaches the Volume to the Virtual Machine.
description:
  - This playbook helps in performing the Volume detach operations on the VM provided.
options:
  name:
    description:
      - Name of the VM
    required: true
    type: str
  id:
    description:
      - ID of the VM
    type: str
  volume_name:
    description:
      - Name of the volumes want to be detached
    type: list
  volume_id:
    description:
      - IDs of the volumes want to be detached
    type: list

'''

EXAMPLES = '''
  - name: VM Volume Detach Playbook
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
       - name: Perform VM Volume Attach Operations
         ibm.powervc.volume_detach:
            auth: "{{ auth }}"
            name: "NAME"
            volume_name: ["VOL_NAME1","VOL_NAME2","VOL_NAME3"]
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Volume Detach Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Volume Attach Operations
         ibm.powervc.volume_detach:
            cloud: "CLOUD_NAME"
            name: "NAME"
            volume_name: ["VOLUME_NAME1","VOLUME_NAME2","VOLUME_NAME3"]
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Volume Detach Playbook using the Volume IDs
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Volume Attach Operations
         ibm.powervc.volume_detach:
            cloud: "CLOUD_NAME"
            name: "NAME"
            volume_name: ["VOLUME_ID1","VOLUME_ID2","VOLUME_ID3"]
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_volume_detach import volume_ops


class VolumeDetachVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        volume_name=dict(type='list'),
        volume_id=dict(type='list'),
    )
    module_kwargs = dict(
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'id'], ['volume_name', 'volume_id']
        ]
    )

    def run(self):
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        vm_name = self.params['name']
        vm_id = self.params['id']
        vol_name = self.params['volume_name']
        vol_id = self.params['volume_id']
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        if vol_name:
            vol_id = []
            for name in vol_name:
                vol_id.append(self.conn.block_storage.find_volume(name, ignore_missing=False).id)
        try:
            res = volume_ops(self, self.conn, authtoken, tenant_id, vm_id, vol_id)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = VolumeDetachVMModule()
    module()


if __name__ == '__main__':
    main()
