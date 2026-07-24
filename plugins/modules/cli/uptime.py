#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: uptime
author:
    - Yogita Garani (@yogita.garani1)
short_description: Get system uptime from PowerVC Controller
description:
  - This module retrieves system boot time and uptime information from the PowerVC Controller
  - Uses C(who -b) command to get the last system boot time
options:
  login_host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot))
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user
    required: true
    type: str
    no_log: true
'''

EXAMPLES = '''
- name: Get PowerVC uptime
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Retrieve system boot time from PowerVC Controller
      ibm.powervc.cli.uptime:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result

    - name: Display uptime information
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether any changes were made (always false for uptime queries)
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string
  returned: always
  type: str
stdout_lines:
  description: Command output split into lines
  returned: always
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_uptime(module):
    '''Execute the uptime command on the PowerVC controller'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']

    connection = Connection(module, host_ip, user, password, command="who -b")

    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(msg="Failed to retrieve system uptime information", stderr=stderr_msg)

    lines = output if isinstance(output, list) else [str(output)]

    module.exit_json(
        changed=False,
        stdout="\n".join(lines),
        stdout_lines=lines,
        msg="Successfully retrieved system uptime information"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout="",
            stdout_lines=[],
            msg="[CHECK MODE] Would retrieve system uptime information"
        )

    run_uptime(module)


if __name__ == '__main__':
    main()
