#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: pvcmon
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Monitor PowerVC node resources
description:
  - This module monitors PowerVC node memory, processor, disk, swap, and inode usage
  - Supports real-time monitoring with configurable intervals
  - Can perform one-time checks or continuous monitoring
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
  resource:
    description:
      - Resource type to monitor
    required: true
    type: str
    choices: ['disk', 'proc', 'mem', 'swap', 'inode']
  interval:
    description:
      - Interval in seconds for monitoring updates
      - If not specified, uses default behavior (4 seconds)
      - Set to C(0) for single snapshot
      - Set to a positive integer for continuous monitoring at that interval
    type: int
    required: false
'''

EXAMPLES = '''
- name: Monitor PowerVC disk usage
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Get disk usage snapshot
      ibm.powervc.cli.pvcmon:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        resource: "disk"
        interval: 0
      register: result

    - name: Display disk monitoring output
      debug:
        var: result.stdout_lines


- name: Monitor PowerVC memory usage with interval
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Monitor memory at 5-second intervals
      ibm.powervc.cli.pvcmon:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        resource: "mem"
        interval: 5
      register: result

    - name: Display memory monitoring output
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether any changes were made (always false for monitoring operations)
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


def run_pvcmon(module):
    '''Execute the pvcmon command on the PowerVC controller'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    resource = module.params['resource']
    interval = module.params['interval']

    command = f"pvcmon -r {resource}"
    if interval is not None:
        command += f" -n {interval}"

    connection = Connection(module, host_ip, user, password, command=command)

    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(msg="pvcmon command failed", stderr=stderr_msg)

    lines = output if isinstance(output, list) else [str(output)]

    if interval == 0:
        msg = f"Successfully retrieved {resource} monitoring snapshot"
    else:
        msg = f"Successfully monitored {resource} usage"

    module.exit_json(
        changed=False,
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
            resource=dict(type='str', required=True, choices=[
                'disk', 'proc', 'mem', 'swap', 'inode']),
            interval=dict(type='int', required=False),
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would monitor {module.params['resource']} usage"
        )

    run_pvcmon(module)


if __name__ == '__main__':
    main()
