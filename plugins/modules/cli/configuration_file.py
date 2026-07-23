#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: configuration_file
author:
    - Yogita Garani (@yogita.garani1)
short_description: Change configuration files in PowerVC
description:
  - This module manipulates key-value pairs in PowerVC configuration files
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
      - State of the configuration operation
    type: str
  action:
    description:
      - Action to perform on the configuration file (add/modify)
    type: str
  filename:
    description:
      - Configuration filename
    required: true
    type: str
  section:
    description:
      - Section Name
    required: true
    type: str
  parameter:
    description:
      - Parameter name
    required: true
    type: str
  value:
    description:
      - Value for the parameter
    type: str
  restart:
    description:
      - Argument to restart the service (yes/no)
    type: str
"""

EXAMPLES = """
---
- name: "Change Configuration Files"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Add key-value pair to a configuration file"
      ibm.powervc.cli.configuration_file:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        action: add
        filename: "{{ filename }}"
        section: "{{ section }}"
        parameter: "{{ parameter }}"
        value: "{{ value }}"
        restart: "{{ restart }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

---
- name: "Change Configuration Files"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Modify an existing key-value pair in a configuration file"
      ibm.powervc.cli.configuration_file:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        action: modify
        filename: "{{ filename }}"
        section: "{{ section }}"
        parameter: "{{ parameter }}"
        value: "{{ value }}"
        restart: "{{ restart }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

---
- name: "Change Configuration Files"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Remove a key-value pair from a configuration file"
      ibm.powervc.cli.configuration_file:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: absent
        filename: "{{ filename }}"
        section: "{{ section }}"
        parameter: "{{ parameter }}"
        restart: "{{ restart }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

---
- name: "Change Configuration Files"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Modify an existing key-value pair in a configuration file"
      ibm.powervc.cli.configuration_file:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        action: modify
        filename: "{{ filename }}"
        section: "{{ section }}"
        parameter: "{{ parameter }}"
        value: "{{ value }}"
        restart: "yes"
      register: result

    - name: "Show stdout"
      debug:
        var: result
"""
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule

# Execution


def compose_command(state, filename, action=None, section=None, parameter=None, value=None, restart='no'):
    """
    Construct the command based on the parameters

    :param str state: state of the key-value pair
    :param str action: action to perform on the key-value pair
    :param str filename: configuration filename
    :param str section: section in the configuration file
    :param str parameter: parameter in the configuration file
    :param str value: value corresponding to the parameter
    :param str restart: flag to restart the service
    :return str, dict command, messages: Return the constructed command and its messages
    """
    command = None
    messages = {}
    if state == "absent" and action:
        return command, messages
    if state == "absent" and action is None:
        action = "remove"
    command = f"powervc-configmod {action} --filename={filename}"
    if section:
        command += f" --section={section}"
    if parameter:
        command += f" --parameter={parameter}"
    if value:
        command += f" --value={value}"
    if restart == 'yes':
        command += " --restart"
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """

    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            state=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            action=dict(type='str', required=False, default=None,
                        choices=["add", "modify", None]),
            filename=dict(type='str', required=True),
            section=dict(type='str', required=True),
            parameter=dict(type='str', required=True),
            value=dict(type='str', required=False, default=None),
            restart=dict(type='str', required=False,
                         default='no', choices=['no', 'yes']),
        )
    )
    host_ip = module.params['login_host']
    state = module.params['state']
    user = module.params['login_user']
    password = module.params['login_password']
    action = module.params['action']
    filename = module.params['filename']
    section = module.params['section']
    parameter = module.params['parameter']
    value = module.params['value']
    restart = module.params['restart']
    output = None
    changed = False
    failed = True

    command, messages = compose_command(
        state, filename, action, section, parameter, value, restart)
    if command is None and not messages:
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
        module.fail_json(msg=msg)
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
