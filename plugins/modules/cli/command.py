#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: backup
author:
    - Yogita Garani (@yogita.garani1)
short_description: Take a backup on PowerVC
description:
  - This module performs backup operation on the PowerVC Controller
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
  command:
    description:
      - Command to be executed
    required: true
    type: str
  messages:
    description:
      - Optional input messages and corresponding values
    type: dict

"""

EXAMPLES = """
---
- name: "Remote command execution"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Run command on PowerVC Controller"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "{{ command }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result.stdout_lines

---
- name: "Remote command execution"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Run a command with input messages"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "powervc-opsmgr restore -c siva1234"
        messages:
          'Last successful backup at (.)*(\n)*(\\s)*Do you want to continue restoring the backup? [Y/N]:(\\s)*': 'y'
      register: result

    - name: "Show stdout"
      debug:
        var: result.stdout_lines
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            command=dict(type='str', required=True),
            messages=dict(type='dict', required=False, default={}),
            state=dict(type='str', required=False, default='present'),
        )
    )
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    command = module.params['command']
    messages = module.params['messages']

    output = None
    changed = False
    if messages == "" or messages == {} or messages is None:
        messages = {}
    if command is None:
        module.fail_json(failed=True, changed=False, msg="Wrong arguments")
    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
    try:
        rc, output = connection.run()
        if int(rc) != 0:
            changed = False
            failed = True
        else:
            changed = True
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

    if output and rc == 0:
        result['stdout_lines'] = output
        result['msg'] = "Operation completed successfully"
    else:
        result['warning'] = output
        result['msg'] = "Operation did not complete successfully"
    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
