#!/usr/bin/python
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: uptime
author:
    - Yogita Garani (@yogita.garani1)
short_description: Get system uptime from PowerVC Controller
description:
  - This module retrieves system boot time and uptime information from the PowerVC Controller
  - Uses 'who -b' command to get the last system boot time
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
      - State of uptime operation (always present)
    type: str
    default: present
"""

EXAMPLES = """
---
- name: "Get PowerVC Uptime"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Get system uptime from PowerVC Controller"
      ibm.powervc.cli.uptime:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result

    - name: "Show uptime information"
      debug:
        var: result
"""


def construct_command():
    """
    Construct the uptime command

    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {}
    command = "who -b"
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=False, choices=[
                       'present'], default='present'),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
        )
    )

    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    output = None
    changed = False
    failed = True

    command, messages = construct_command()

    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
    try:
        rc, output = connection.run()
        if int(rc) != 0:
            changed = False
            failed = True
        else:
            changed = False
            failed = False
    except (CLIError, Exception) as e:
        msg = str(e)
        module.fail_json(failed=True, msg=msg)

    result = dict(
        changed=False,
        failed=True,
        warning=False,
        stdout_lines="",
        error="",
        rc=1,
        msg=''
    )
    result['changed'] = changed
    result['failed'] = failed
    result['rc'] = int(rc)

    if output and not failed:
        result['stdout_lines'] = output
        result['msg'] = "Successfully retrieved system uptime information"
    else:
        result['warning'] = output
        result['msg'] = "Failed to retrieve system uptime information"

    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
