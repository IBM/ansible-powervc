#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: scg_operations
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Create, Delete, Update the SCG Details.
description:
  - This playbook helps in performing the Create, Delete and Update operations for the Storage Connectivity Groups.
options:
  state:
    description:
      - SCG Operation to be perfomed
    choices: [absent, present]
    required: yes
    type: str
  name:
    description:
      - Name of the Storage Connectivity Group
    type: str
  scg_id:
    description:
      - ID of the Storage Connectivity Group
    type: str
'''

EXAMPLES = '''
  - name: Storage Connectivity Group Operations from PowerVC Server
    hosts: all
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
       - name: Performing the DELETE SCG Operation
         ibm.powervc.scg_operations:
            auth: "{{ auth }}"
            state: "absent"
            name: "NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: Storage Connectivity Group Operations from PowerVC Server
    hosts: all
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
       - name: Performing the Create SCG Operation
         ibm.powervc.scg_operations:
            auth: "{{ auth }}"
            state: "present"
            display_name: <DISPLAY_NAME>
            vios_ids: <VIOS_ID>
            boot_connectivity: <BOOT_CONNECTIVITY_VAL>
            data_connectivity: <DATA_CONNECTIVITY_VAL>
         register: result
       - debug:
            var: result

  - name: Storage Connectivity Group Operations from PowerVC Server
    hosts: all
    gather_facts: no
    tasks:
       - name: Performing the Create SCG Operation
         ibm.powervc.scg_operations:
            cloud: "{{ CLOUD_NAME }}"
            state: "present"
            display_name: <DISPLAY_NAME>
            vios_ids: <VIOS_ID>
            boot_connectivity: <BOOT_CONNECTIVITY_VAL>
            data_connectivity: <DATA_CONNECTIVITY_VAL>
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_scg import scg_ops


class SCGOpsModule(OpenStackModule):
    argument_spec = dict(
        name=dict(required=False),
        id=dict(required=False),
        state=dict(required=False),
        action=dict(),
        auto_add_vios=dict(),
        fc_storage_access=dict(type='bool'),
        boot_connectivity=dict(type='list'),
        data_connectivity=dict(type='list'),
        vios_ids=dict(type='list'),
        enabled=dict(type='bool'),
        display_name=dict(),
        exact_redundancy=dict(type='bool'),
        ports_per_fabric_npiv=dict(type='bool'),
        fabric_set_req=dict(),
        fabric_set_npiv=dict(type='bool'),
        port_tag=dict(),
        include_untagged=dict(type='bool'),
        vios_redundancy=dict(type='bool'),
        cluster_provider_name=dict(),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        name = self.params['name']
        state = self.params['state']
        action = self.params['action']
        auto_add_vios = self.params['auto_add_vios']
        include_untagged = self.params['include_untagged']
        scg_id = self.params['id']
        fc_storage_access = self.params['fc_storage_access']
        boot_connectivity = self.params['boot_connectivity']
        data_connectivity = self.params['data_connectivity']
        vios_redundancy = self.params['vios_redundancy']
        exact_redundancy = self.params['exact_redundancy']
        vios_ids = self.params['vios_ids']
        enabled = self.params['enabled']
        display_name = self.params['display_name']
        cluster_provider_name = self.params['cluster_provider_name']
        fabric_set_req = self.params['fabric_set_req']
        fabric_set_npiv = self.params['fabric_set_npiv']
        port_tag = self.params['port_tag']
        ports_per_fabric_npiv = self.params['ports_per_fabric_npiv']
        tenant_id = self.conn.session.get_project_id()
        try:
            data = {"storage_connectivity_group": {
                    "auto_add_vios": auto_add_vios,
                    "include_untagged": include_untagged,
                    "fc_storage_access": fc_storage_access,
                    "boot_connectivity": boot_connectivity,
                    "data_connectivity": data_connectivity,
                    "vios_ids": vios_ids,
                    "enabled": enabled,
                    "display_name": display_name,
                    "cluster_provider_name": cluster_provider_name,
                    "vios_redundancy": vios_redundancy,
                    "exact_redundancy": exact_redundancy,
                    "ports_per_fabric_npiv": ports_per_fabric_npiv,
                    "fabric_set_req": fabric_set_req,
                    "fabric_set_npiv": fabric_set_npiv,
                    "port_tag": port_tag}}
            res = scg_ops(self, self.conn, authtoken, state, action, tenant_id, name, scg_id, data)
            self.exit_json(changed=False, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = SCGOpsModule()
    module()


if __name__ == '__main__':
    main()
