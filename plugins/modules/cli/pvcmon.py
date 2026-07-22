#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
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
      - SSH User (pvcroot)
    required: true
    type: str
  login_password:
    description:
      - Password for the ssh user
    required: true
    type: str
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
      - Set to 0 for single snapshot
      - Set to positive integer for continuous monitoring at that interval
    type: int
    required: false
  state:
    description:
      - State of monitoring operation (always present)
    type: str
    default: present
"""

EXAMPLES = """
---
- name: "Monitor PowerVC Resources"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: ""Monitor resource usage with specified interval"
      ibm.powervc.cli.pvcmon:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        resource: "{{ resource }}"
        interval: "{{ interval }}"
      register: result

    - name: "Show monitoring output"
      debug:
        var: result.stdout_lines

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def construct_command(resource, interval):
    """
    Construct the pvcmon command

    :param str resource: Resource type to monitor (disk, proc, mem, swap, inode)
    :param int interval: Interval in seconds
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {}
    command = f"pvcmon -r {resource}"

    if interval is not None:
        command += f" -n {interval}"

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
            resource=dict(type='str', required=True, choices=[
                'disk', 'proc', 'mem', 'swap', 'inode']),
            interval=dict(type='int', required=False),
        )
    )

    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    resource = module.params['resource']
    interval = module.params['interval']

    output = None
    changed = False
    failed = True

    command, messages = construct_command(resource, interval)

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
        if interval == 0:
            result['msg'] = f"Successfully retrieved {resource} monitoring snapshot"
        else:
            result['msg'] = f"Successfully monitored {resource} usage"
    else:
        result['warning'] = output
        result['msg'] = f"Failed to monitor {resource} usage"

    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
