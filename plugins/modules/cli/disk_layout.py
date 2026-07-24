#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: disk_layout
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Display disk partition layout on the PowerVC Controller
description:
  - This module displays fdisk partition information for the PowerVC Controller.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH User (pvcroot)
    required: true
    type: str
  login_password:
    description:
      - Password for the ssh user
    required: true
    type: str
  state:
    description:
      - Always C(list) — lists the fdisk partitions. Only value accepted.
    required: true
    type: str
    choices: ['list']
'''

EXAMPLES = '''
- name: "Show disk layout"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Show the disk layout"
      ibm.powervc.cli.disk_layout:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "list"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether a change was made (always false for list).
  returned: always
  type: bool
rc:
  description: Return code from the command.
  returned: always
  type: int
stdout_lines:
  description: Command output split into lines.
  returned: success
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_disk_layout(module):
    ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']

    command = "chpvc fdisk list"

    if module.check_mode:
        module.exit_json(changed=False, rc=0, stdout_lines=[],
                         msg=f"[CHECK MODE] Would run: {command}")

    connection = Connection(module, ip, user, password, command=command)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e), changed=False)

    if int(rc) != 0:
        module.fail_json(
            msg=f"Disk layout command failed with rc={rc}",
            rc=int(rc),
            stderr=output,
            changed=False
        )

    module.exit_json(
        changed=False,
        rc=int(rc),
        stdout_lines=output if output else [],
        msg="Disk layout retrieved successfully"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            state=dict(type='str', required=True, choices=['list']),
        ),
        supports_check_mode=True
    )
    run_disk_layout(module)


if __name__ == '__main__':
    main()
