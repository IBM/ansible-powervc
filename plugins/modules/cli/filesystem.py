#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: filesystem
author:
    - Yogita Garani (@yogita.garani1)
short_description: Manage filesystems on the PowerVC Controller
description:
  - This module manages PowerVC filesystems on the Controller over SSH.
  - Use C(state=list) to display filesystem information, with an optional
    C(json_format=yes) flag for machine-readable output.
  - Use C(state=free) to release filesystem space by age (C(days)/C(hours))
    or by size (C(size)). At least one of C(days), C(hours), or C(size)
    must be supplied when using C(state=free).
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
      - Operation to perform. C(list) displays filesystem information.
        C(free) releases space from a filesystem.
    required: true
    type: str
    choices: ['list', 'free']
  filesystem_name:
    description:
      - Name of the filesystem to target. If omitted all filesystems
        are listed. Only used with C(state=list).
    required: false
    type: str
    choices:
      - /powervchome
      - /dump
      - /extra
      - /powervcdata
      - /powervclog
  days:
    description:
      - Number of days of data to free. Used with C(state=free).
    required: false
    type: int
  hours:
    description:
      - Number of hours of data to free. Used with C(state=free).
    required: false
    type: int
  size:
    description:
      - Size of data to free (in MB). Used with C(state=free).
    required: false
    type: int
  json_format:
    description:
      - When C(yes), print output in JSON format. Only used with C(state=list).
    required: false
    type: str
    choices: ['yes', 'no']
    default: 'no'
'''

EXAMPLES = '''
- name: "Filesystem Management - list all filesystems"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List all filesystems"
      ibm.powervc.cli.filesystem:
        state: "list"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result
    - name: "Show output"
      debug:
        var: result

- name: "Filesystem Management - list specific filesystem in JSON"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List filesystem in JSON format"
      ibm.powervc.cli.filesystem:
        state: "list"
        json_format: "yes"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        filesystem_name: "/powervclog"
      register: result
    - name: "Show output"
      debug:
        var: result

- name: "Filesystem Management - free space"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Free filesystem space older than 7 days"
      ibm.powervc.cli.filesystem:
        state: "free"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        days: 7
      register: result
    - name: "Show output"
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the operation executed successfully.
  returned: always
  type: bool
rc:
  description: Return code from the filesystem command.
  returned: always
  type: int
stdout_lines:
  description: Command output split into a list of lines.
  returned: success
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


def construct_command(
        state,
        filesystem=None,
        days=None,
        hours=None,
        size=None,
        json_format="no"):
    '''
    Construct the lspvcfs / chpvcfs command from the given parameters.

    :param str state: 'list' or 'free'
    :param str filesystem: optional filesystem path filter
    :param int days: days of data to free
    :param int hours: hours of data to free
    :param int size: size of data to free (MB)
    :param str json_format: 'yes' or 'no'
    :return tuple(str|None, dict): (command, messages)
    '''
    command = None

    if state == 'list':
        command = "lspvcfs list-filesystems"
        if json_format == 'yes':
            command += " --json"
        if filesystem is not None:
            command += f" --filesystem {filesystem}"

    elif state == "free":
        if not any([days, hours, size]):
            # No free parameters supplied — caller will fail_json
            return None, {}
        command = "chpvcfs -o f"
        if days is not None:
            command += f" -d {days}"
        if hours is not None:
            command += f" -hr {hours}"
        if size is not None:
            command += f" -s {size}"

    return command, {}


def run_filesystem(module):
    '''
    Execute the filesystem command on the PowerVC Controller.

    :param module: AnsibleModule instance
    '''
    state = module.params['state']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    filesystem = module.params['filesystem_name']
    days = module.params['days']
    hours = module.params['hours']
    size = module.params['size']
    json_format = module.params['json_format']

    command, messages = construct_command(
        state, filesystem, days, hours, size, json_format)

    if command is None:
        if state == 'free':
            module.fail_json(
                changed=False,
                msg="state=free requires at least one of: days, hours, size"
            )
        else:
            module.fail_json(
                changed=False,
                msg=f"Invalid state '{state}'. Expected one of: list, free"
            )

    # check_mode: list is read-only (changed=False); free would mutate (changed=True)
    if module.check_mode:
        module.exit_json(
            changed=(state == "free"),
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        module.fail_json(
            msg=f"Filesystem operation failed with rc={rc}",
            rc=int(rc),
            stderr=output,
            changed=False
        )

    if not output:
        module.warn("Filesystem operation returned no output")

    # list is a read-only inspection; free actually releases space
    module.exit_json(
        changed=(state == "free"),
        rc=int(rc),
        stdout_lines=output if output else [],
        msg="Operation completed successfully"
    )


def main():
    '''
    Main execution
    '''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True, choices=['list', 'free']),
            login_host=dict(type='str', required=True),
            # F-unique: login_user must NOT have no_log — it is not a secret
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            filesystem_name=dict(type='str', required=False, default=None, choices=[
                None,
                '/powervchome',
                '/dump',
                '/extra',
                '/powervcdata',
                '/powervclog'
            ]),
            # F-unique: days/hours/size must be int to match DOCUMENTATION
            days=dict(type='int', required=False, default=None),
            hours=dict(type='int', required=False, default=None),
            size=dict(type='int', required=False, default=None),
            json_format=dict(type='str', required=False,
                             default='no', choices=['yes', 'no']),
        ),
        supports_check_mode=True
    )
    run_filesystem(module)


if __name__ == '__main__':
    main()
