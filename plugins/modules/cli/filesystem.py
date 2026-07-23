#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: filesystem
author:
    - Yogita Garani (@yogita.garani1)
short_description: Manage filesystems in PowerVC
description:
  - This module manages PowerVC filesystems on the Controller
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
      - State of the filesystem operation
    required: true
    type: str
  filesystem_name:
    description:
      - Name of the filesystem
    type: str
  days:
    description:
      - Number of days of data to free
    type: int
  hours:
    description:
      - number of hours of data to free
    type: int
  size:
    description:
      - Size of data to free
    type: int
  json_format:
    description:
      - Flag to print output in json format (yes/no)
    type: str
"""

EXAMPLES = """
---
- name: "PowerVC Filesystem Management"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "List Filesystem"
      ibm.powervc.cli.filesystem:
        state: "list"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        filesystem_name: "{{ filesystem }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

---
- name: "PowerVC Filesystem Management"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "List Filesystems in json format"
      ibm.powervc.cli.filesystem:
        state: list
        json_format: "yes"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        filesystem_name: "{{ filesystem }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result


---
- name: "PowerVC Filesystem Management"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Free space in a filesystem"
      ibm.powervc.cli.filesystem:
        state: "free"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        days: "{{ days }}"
        hours: "{{ hours }}"
        size: "{{ size }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result
"""
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(
        state,
        filesystem=None,
        days=None,
        hours=None,
        size=None,
        json_format="no"):
    """
    Construct the command based on the parameters

    :param str state: state
    :param str filesystem: filesystem to run operation on
    :param str days: Number of days data to free
    :param str hours: Number of hours data to free
    :param str size: Size of data to free
    :param str output_format: Print output in json format
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {}
    command = None
    if state == 'list' and json_format == 'no':
        if filesystem is None:
            command = "lspvcfs list-filesystems"
        else:
            command = f"lspvcfs list-filesystems --filesystem {filesystem}"
    elif state == 'list' and json_format == 'yes':
        if filesystem is None:
            command = "lspvcfs list-filesystems --json"
        else:
            command = f"lspvcfs list-filesystems --json --filesystem {filesystem}"
    elif state == "free":
        if any([days, hours, size]):
            command = "chpvcfs -o f"
            if days is not None:
                command += f" -d {days}"
            if hours is not None:
                command += f" -hr {hours}"
            if size is not None:
                command += f" -s {size}"
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True, no_log=True),
            login_password=dict(type='str', required=True, no_log=True),
            filesystem_name=dict(type='str', required=False, default=None, choices=[
                None,
                '/powervchome',
                '/dump',
                '/extra',
                '/powervcdata',
                '/powervclog'
            ]),
            days=dict(type='str', required=False, default=None),
            hours=dict(type='str', required=False, default=None),
            size=dict(type='str', required=False, default=None),
            json_format=dict(type='str', required=False,
                             default='no', choices=['yes', 'no']),
        )
    )
    state = module.params['state']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    filesystem = module.params['filesystem_name']
    days = module.params['days']
    hours = module.params['hours']
    size = module.params['size']
    json_format = module.params['json_format']

    output = None
    changed = False
    failed = True

    command, messages = construct_command(
        state, filesystem, days, hours, size, json_format)
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

    if output:
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
