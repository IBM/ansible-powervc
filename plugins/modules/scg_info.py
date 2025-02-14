#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: scg_info
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: To Fetch the SCG Details.
description:
  - This playbook helps in performing the Get operations for the Storage Connectivity Groups.
options:
  scg_name:
    description:
      - Name of the Storage Connectivity Group
    type: str
  scg_id:
    description:
      - ID of the Storage Connectivity Group
    type: str
'''

EXAMPLES = '''

  - name: List all the SCG Details Playbook
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
       - name: Get All the SCG Details
         ibm.powervc.scg_info:
            auth: "{{ auth }}"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: List all the SCG Details Playbook
    hosts: all
    gather_facts: no
    tasks:
       - name: Get All the SCG Details
         ibm.powervc.scg_info:
            cloud: "CLOUD_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result

  - name: List a Specific SCG Details Playbook
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
       - name: Get the specific SCG Details
         powervc.cloud.scg_info:
            auth: "{{ auth }}"
            scg_name: "SCG_NAME"
            validate_certs: no
         register: result
       - debug:
            var: result
'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_scg_info import scg_ops


class SCGInfoModule(OpenStackModule):
    argument_spec = dict(
        scg_name=dict(required=False),
        scg_id=dict(required=False),
    )
    module_kwargs = dict(
        supports_check_mode=True
    )

    def run(self):
        authtoken = self.conn.auth_token
        name = self.params['scg_name']
        # scg_id = self.params['scg_id']
        tenant_id = self.conn.session.get_project_id()
        try:
            res = scg_ops(self, self.conn, authtoken, tenant_id, name)
            self.exit_json(changed=False, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = SCGInfoModule()
    module()


if __name__ == '__main__':
    main()
