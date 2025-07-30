#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: snapshot_info
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Fetches the Snapshot Details
description:
  - This playbook helps in performing the Snapshot Fetch operations on the Snapshot provided.
options:
  name:
    description:
      - Name of the Snapshot
    required: true
    type: str
  id:
    description:
      - ID of the Snapshot
    type: str

'''

EXAMPLES = '''
  - name: Snapshot Details Playbook
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
       - name: Perform Snapshot Details Operation
         ibm.powervc.snapshot_info:
            auth: "{{ auth }}"
            name: "SNAPSHOT_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Snapshot Details Playbook using Snapshot Name
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Snapshot Details Operation
         ibm.powervc.snapshot_info:
            cloud: "CLOUD_NAME"
            id: "SNAPSHOT_ID"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Snapshot Details Playbook using the Snapshot IDs
    hosts: localhost
    gather_facts: no
    tasks:
       - name: Perform Snapshot Details Operation
         ibm.powervc.snapshot_info:
            cloud: "CLOUD_NAME"
            name: "SNAPSHOT_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_snapshot_info import snapshot_ops


class SnapshotInfoModule(OpenStackModule):
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
        snapshot_name = self.params['name']
        snapshot_id = self.params['id']
        if snapshot_name:
            snapshot_id = self.conn.block_storage.find_snapshot(snapshot_name, ignore_missing=False).id
        try:
            res = snapshot_ops(self, self.conn, authtoken, tenant_id, snapshot_id)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=True)


def main():
    module = SnapshotInfoModule()
    module()


if __name__ == '__main__':
    main()
