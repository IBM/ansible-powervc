#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: ping
author:
    - Yogita Garani (@yogita.garani1)
short_description: Ping PowerVC Controller from Ansible controller
description:
  - This module performs ping operation from the Ansible controller to the PowerVC Controller
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
      - Timeout in seconds for each ping
    required: false
    type: int
  state:
    description:
      - State of ping operation, always present
    type: str
    default: present
"""

EXAMPLES = """
---
- name: "Ping PowerVC Controller"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml

  tasks:
    - name: "Ping PowerVC from Ansible controller"
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
      register: result

    - name: "Show ping result"
      debug:
        var: result


- name: "Ping PowerVC with custom count"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml

  tasks:
    - name: "Ping PowerVC with 10 packets"
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
        count: 10
      register: result

    - name: "Show ping result"
      debug:
        var: result


- name: "Ping PowerVC with timeout"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml

  tasks:
    - name: "Ping PowerVC with timeout"
      ibm.powervc.cli.ping:
        login_host: "{{ ipaddress }}"
        count: 5
        timeout: 2
      register: result

    - name: "Show ping result"
      debug:
        var: result
"""
from ansible.module_utils.basic import AnsibleModule


def construct_command(target_host, count=4, timeout=None):
    """
    Construct the ping command based on the parameters

    :param str target_host: target host IP or hostname
    :param int count: number of ping packets
    :param int timeout: timeout in seconds
    :return str command: Return the constructed ping command
    """
    command = f"ping -c {count}"
    if timeout is not None:
        command += f" -W {timeout}"
    command += f" {target_host}"
    return command


def run_ping():
    """
    Read all arguments from the ansible module and execute ping from the Ansible controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=False, choices=[
                       'present'], default='present'),
            login_host=dict(type='str', required=True),
            count=dict(type='int', required=False, default=4),
            timeout=dict(type='int', required=False, default=None),
        )
    )

    host_ip = module.params['login_host']
    count = module.params['count']
    timeout = module.params['timeout']

    command = construct_command(host_ip, count, timeout)

    try:
        # Execute ping command from Ansible controller
        rc, stdout, stderr = module.run_command(command)

        result = dict(
            changed=False,
            failed=False,
            rc=rc,
            stdout_lines=stdout.split('\n') if stdout else [],
            stderr=stderr if stderr else '',
            msg=''
        )

        if rc == 0:
            result['msg'] = f"Ping to {host_ip} successful"
            result['failed'] = False
        else:
            result['msg'] = f"Ping to {host_ip} failed - host may be unreachable"
            result['failed'] = True

        module.exit_json(**result)

    except Exception as e:
        module.fail_json(msg=f"Ping operation failed: {str(e)}", rc=1)


def main():
    """
    Main execution
    """
    run_ping()


if __name__ == '__main__':
    main()
