#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: ping
author:
    - Yogita Garani (@yogita.garani1)
short_description: Ping PowerVC Controller from Ansible controller
description:
  - This module performs a ping operation from the Ansible controller to the PowerVC Controller
  - Tests network connectivity to PowerVC
options:
  login_host:
    description:
      - IP address of the PowerVC Controller to ping
    required: true
    type: str
  count:
    description:
      - Number of ping packets to send
    required: false
    type: int
    default: 4
  timeout:
    description:
      - Timeout in seconds for each ping attempt
    required: false
    type: int
'''

EXAMPLES = '''
- name: Ping PowerVC Controller
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
  tasks:
    - name: Ping PowerVC with default packet count
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
      register: result

    - name: Display ping result
      debug:
        var: result


- name: Ping PowerVC with custom count
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
  tasks:
    - name: Ping PowerVC with 10 packets
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
        count: 10
      register: result

    - name: Display custom count ping result
      debug:
        var: result


- name: Ping PowerVC with timeout
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
  tasks:
    - name: Ping PowerVC with 5 packets and 2-second timeout
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
        count: 5
        timeout: 2
      register: result

    - name: Display timeout ping result
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether any changes were made (always false for ping operations)
  returned: always
  type: bool
rc:
  description: Return code from the ping command
  returned: always
  type: int
stdout_lines:
  description: Ping command output split into lines
  returned: always
  type: list
  elements: str
stderr:
  description: Standard error output from the ping command
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule


def run_ping(module):
    '''Execute ping from the Ansible controller to the target host'''
    host_ip = module.params['login_host']
    count = module.params['count']
    timeout = module.params['timeout']

    command = f"ping -c {count}"
    if timeout is not None:
        command += f" -W {timeout}"
    command += f" {host_ip}"

    try:
        rc, stdout, stderr = module.run_command(command)
    except Exception as e:
        module.fail_json(msg=f"Ping operation failed: {str(e)}", rc=1)

    if rc == 0:
        msg = f"Ping to {host_ip} successful"
        failed = False
    else:
        msg = f"Ping to {host_ip} failed - host may be unreachable"
        failed = True

    module.exit_json(
        changed=False,
        failed=failed,
        rc=rc,
        stdout_lines=stdout.split('\n') if stdout else [],
        stderr=stderr if stderr else '',
        msg=msg
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            count=dict(type='int', required=False, default=4),
            timeout=dict(type='int', required=False, default=None),
        ),
        supports_check_mode=True
    )

    if module.check_mode:
        module.exit_json(
            changed=False,
            rc=0,
            stdout_lines=[],
            stderr='',
            msg=f"[CHECK MODE] Would ping {module.params['login_host']}"
        )

    run_ping(module)


if __name__ == '__main__':
    main()
