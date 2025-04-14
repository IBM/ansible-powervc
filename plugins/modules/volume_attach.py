#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: volume_attach
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Attach the Volume to the Virtual Machine.
description:
  - This playbook helps in performing the Volume attach operations on the VM provided. Bulk Volume Attach API call is used for this operation.
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
      - Name of the volumes want to be attached
    type: list
  volume_id:
    description:
      - IDs of the volumes want to be attached
    type: list

'''

EXAMPLES = '''
---
  - name: VM Volume Attach Playbook
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
         ibm.powervc.volume_attach:
            auth: "{{ auth }}"
            name: "NAME"
            volume_name: ["VOL_NAME1","VOL_NAME2","VOL_NAME3"]
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: VM Volume Attach Playbook
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform VM Volume Attach Operations
         ibm.powervc.volume_attach:
            cloud: "CLOUD_NAME"
            name: "NAME"
            volume_name: ["VOL_NAME1","VOL_NAME2","VOL_NAME3"]
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_volume_attach import volume_ops


class VolumeAttachVMModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        volume_name=dict(type='list'),
        volume_id=dict(type='list'),
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
        vol_name = self.params['volume_name']
        volume_id = self.params['volume_id']
        if vm_name:
            vm_id = self.conn.compute.find_server(vm_name, ignore_missing=False).id
        if vol_name:
            vol_ids = []
            for name in vol_name:
                vol_ids.append(self.conn.block_storage.find_volume(name, ignore_missing=False).id)
            vol_data = {"volumeAttachment": [{"volumeId": vol_id} for vol_id in vol_ids]}
        elif volume_id:
            vol_data = {"volumeAttachment": [{"volumeId": vol_id} for vol_id in volume_id]}
        try:
            data = {"bulkVolumeAttach": vol_data}
            res = volume_ops(self, self.conn, authtoken, tenant_id, vm_id, data)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = VolumeAttachVMModule()
    module()


if __name__ == '__main__':
    main()
