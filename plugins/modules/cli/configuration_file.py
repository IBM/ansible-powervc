#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: configuration_file
author:
    - Yogita Garani (@yogita.garani1)
short_description: Change configuration files in PowerVC
description:
  - This module manipulates key-value pairs in PowerVC configuration files
    using the C(powervc-configmod) CLI tool.
  - For C(state=present) with C(action=add) or C(action=modify) the module
    B(reads the current value first). If the parameter already holds the
    desired value it returns C(changed=false) without writing — making
    repeated runs idempotent.
  - For C(state=absent) the module checks whether the parameter exists
    before issuing the remove command. If the parameter is already absent
    it returns C(changed=false).
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
  state:
    description:
      - C(present) with C(action=add) or C(action=modify) to add or modify
        a key-value pair.
      - C(absent) to remove a key-value pair.
    required: true
    type: str
    choices: ['present', 'absent']
  action:
    description:
      - Action to perform on the configuration file.
      - C(add) — add a new key-value pair.
      - C(modify) — modify an existing key-value pair.
      - Required when C(state=present).
    type: str
    choices: ['add', 'modify']
  filename:
    description:
      - Configuration filename to modify.
    required: true
    type: str
  section:
    description:
      - Section in the configuration file.
    required: true
    type: str
  parameter:
    description:
      - Parameter name within the section.
    required: true
    type: str
  value:
    description:
      - Value for the parameter (required for C(add) and C(modify)).
    type: str
  restart:
    description:
      - Whether to restart the service after applying the change.
    type: str
    default: 'no'
    choices: ['no', 'yes']
'''

EXAMPLES = '''
- name: Add key-value pair to a configuration file
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Add parameter to config file
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

    - name: Display add result
      debug:
        var: result


- name: Modify an existing key-value pair in a configuration file
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Modify parameter in config file
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

    - name: Display modify result
      debug:
        var: result


- name: Remove a key-value pair from a configuration file
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove parameter from config file
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

    - name: Display remove result
      debug:
        var: result


- name: Modify configuration and restart service
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Modify parameter and restart affected service
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

    - name: Display restart result
      debug:
        var: result
'''

RETURN = '''
changed:
  description: >
    Whether any configuration file change was made.
    False when the parameter already holds the desired value (idempotent),
    when the parameter is already absent, or when running in check_mode.
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string
  returned: when command was executed
  type: str
stdout_lines:
  description: Command output split into lines
  returned: when command was executed
  type: list
  elements: str
current_value:
  description: >
    The value the parameter held before the module ran. C(None) when the
    parameter did not exist or could not be read.
  returned: when state=present and parameter was read
  type: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def compose_command(state, filename, action=None, section=None,
                    parameter=None, value=None, restart='no'):
    '''Construct the powervc-configmod write command.'''
    if state == "absent" and action:
        return None
    if state == "absent":
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
    return command


def _read_current_value(module, host_ip, user, password,
                        filename, section, parameter):
    '''
    Read the current value of a parameter using powervc-configmod get.
    Returns the stripped value string, or None if absent / unreadable.
    '''
    get_cmd = (f"powervc-configmod get --filename={filename}"
               f" --section={section} --parameter={parameter}")
    conn = Connection(module, host_ip, user, password, command=get_cmd)
    rc, output = conn.run()
    if rc != 0:
        return None
    lines = output if isinstance(output, list) else output.splitlines()
    for line in lines:
        line = line.strip()
        if line:
            return line
    return None


def run_config_file(module):
    '''Execute the configuration file command on the PowerVC controller.'''
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

    command = compose_command(state, filename, action, section,
                              parameter, value, restart)

    if command is None:
        module.fail_json(msg="Invalid combination of state and action parameters")

    # ------------------------------------------------------------------ #
    # Idempotency: read current value before writing                       #
    # ------------------------------------------------------------------ #
    current_value = _read_current_value(
        module, host_ip, user, password, filename, section, parameter)

    if state == "present":
        # Already set to the desired value — nothing to do
        if current_value is not None and current_value == (value or '').strip():
            module.exit_json(
                changed=False,
                current_value=current_value,
                msg=f"Parameter '{parameter}' already set to '{current_value}'"
            )

    elif state == "absent":
        # Already absent — nothing to do
        if current_value is None:
            module.exit_json(
                changed=False,
                msg=f"Parameter '{parameter}' is already absent"
            )

    # ------------------------------------------------------------------ #
    # check_mode: report what would change without writing                 #
    # ------------------------------------------------------------------ #
    if module.check_mode:
        if state == "present":
            msg = (f"[CHECK MODE] Would set '{parameter}' to '{value}'"
                   f" in [{section}] of {filename}"
                   f" (current: '{current_value}')")
        else:
            msg = (f"[CHECK MODE] Would remove '{parameter}'"
                   f" from [{section}] of {filename}")
        module.exit_json(
            changed=True,
            current_value=current_value,
            msg=msg
        )

    # ------------------------------------------------------------------ #
    # Execute the write / remove command                                   #
    # ------------------------------------------------------------------ #
    connection = Connection(module, host_ip, user, password, command=command)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(msg="Operation did not complete successfully",
                         stderr=stderr_msg)

    lines = output if isinstance(output, list) else [str(output)]

    module.exit_json(
        changed=True,
        current_value=current_value,
        stdout="\n".join(lines),
        stdout_lines=lines,
        msg="Operation completed successfully"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            state=dict(type='str', required=True, choices=['present', 'absent']),
            action=dict(type='str', required=False, default=None,
                        choices=["add", "modify"]),
            filename=dict(type='str', required=True),
            section=dict(type='str', required=True),
            parameter=dict(type='str', required=True),
            value=dict(type='str', required=False, default=None),
            restart=dict(type='str', required=False,
                         default='no', choices=['no', 'yes']),
        ),
        required_if=[
            ('state', 'present', ['action', 'value']),
        ],
        supports_check_mode=True
    )

    run_config_file(module)


if __name__ == '__main__':
    main()
