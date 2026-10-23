#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: pvcexpand
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: PowerVC LVM auto-expander
description:
  - This module manages LVM disk expansion on the PowerVC Controller using the C(pvcexpand) CLI tool.
  - Use C(state=present) to allocate new disk space (C(--apply)) or simulate expansion when C(dry_run=true) (C(--dry-run)).
  - Use C(state=absent) to display current allocated disk space without making modifications (C(--display)).
  - Supports silent mode execution.
notes:
  - Always take a backup and move it outside of the PowerVC controller before expanding the disk.
  - Do not add and expand a new disk until and unless the current disk is expanded to 2 TB.
  - Expanding a disk beyond 2 TB is not recommended.
  - In case of expanding current used disk, reboot of the node is needed to discover the new volume expanded.
  - Do not remove the disk once added.
  - Shrink of the volume is not allowed.
  - Run with C(state=absent) after running with C(state=present) to fetch the latest disk allotment.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller.
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot)).
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user.
    required: true
    type: str
    no_log: true
  state:
    description:
      - Desired state of the disk expansion.
      - C(present) - Allocate new disk space (modifies disk layout).
      - C(absent) - Display current allocated disk space without modifying anything.
    required: false
    type: str
    choices: ['present', 'absent']
    default: present
  dry_run:
    description:
      - Simulate disk space expansion without making actual changes.
      - Only used when C(state=present).
    required: false
    type: bool
    default: false
  silent:
    description:
      - Run the expansion command in silent mode.
    required: false
    type: bool
    default: false
'''

EXAMPLES = '''
- name: Display current allocated disk space (no modifications)
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Display disk allocation
      ibm.powervc.cli.pvcexpand:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: absent
      register: result

    - name: Show output
      debug:
        var: result.stdout_lines

- name: Simulate disk space allocation (dry run)
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Simulate disk expansion
      ibm.powervc.cli.pvcexpand:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        dry_run: true
      register: result

    - name: Show output
      debug:
        var: result.stdout_lines

- name: Allocate new disk space in silent mode
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Apply disk expansion
      ibm.powervc.cli.pvcexpand:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        silent: true
      register: result

    - name: Show output
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether any disk changes were made (true for apply, false for display and dry_run).
  returned: always
  type: bool
rc:
  description: Return code from the command.
  returned: always
  type: int
stdout:
  description: Raw command output as a single string.
  returned: always
  type: str
stdout_lines:
  description: Command output split into lines.
  returned: always
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError


def construct_command(state, dry_run=False, silent=False):
    """
    Construct the pvcexpand command from given parameters.

    :param str state: 'present' or 'absent'
    :param bool dry_run: whether to simulate disk expansion only
    :param bool silent: whether to pass --silent flag
    :return str: constructed command string
    """
    if state == "present":
        if dry_run:
            cmd = "pvcexpand --dry-run"
        else:
            cmd = "pvcexpand --apply"
    else:
        cmd = "pvcexpand --display"

    if silent:
        cmd += " --silent"

    return cmd


def run_pvcexpand(module):
    """
    Execute the pvcexpand command on the PowerVC Controller.
    """
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    state = module.params['state']
    dry_run = module.params['dry_run']
    silent = module.params['silent']

    command = construct_command(state, dry_run=dry_run, silent=silent)
    is_apply = (state == 'present' and not dry_run)

    if module.check_mode:
        module.exit_json(
            changed=is_apply,
            rc=0,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host_ip, user, password, command=command)

    try:
        rc, output = connection.run()
    except (CLIError, Exception) as e:
        module.fail_json(msg=str(e), changed=False)

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(
            msg=f"pvcexpand command failed with rc={rc}",
            rc=int(rc),
            stderr=stderr_msg,
            changed=False
        )

    lines = output if isinstance(output, list) else ([str(output)] if output else [])

    if state == 'present':
        if dry_run:
            msg = "Disk expansion simulation completed successfully"
        else:
            msg = "Disk expansion allocated successfully"
    else:
        msg = "Current disk allocation retrieved successfully"

    module.exit_json(
        changed=is_apply,
        rc=int(rc),
        stdout="\n".join(lines),
        stdout_lines=lines,
        msg=msg
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            state=dict(
                type='str',
                required=False,
                default='present',
                choices=['present', 'absent']
            ),
            dry_run=dict(type='bool', required=False, default=False),
            silent=dict(type='bool', required=False, default=False),
        ),
        supports_check_mode=True
    )
    run_pvcexpand(module)


if __name__ == '__main__':
    main()
