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
  cluster:
    description:
      - Cluster Name
    required: true
    type: str
  state:
    description:
      - State of backup, always present
    type: str
  preserve:
    description:
      - Number of previous backups to preserve during cleanup
    type: int
  mode:
    description:
      - Mode of logging (silent or verbose)
    type: str
"""

EXAMPLES = """
---
- name: "PowerVC Backup"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Take a backup of the cluster"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        mode: "silent"
      register: result

    - name: "Show stdout"
      debug:
        var: result


- name: "PowerVC Backup"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Take a backup of the cluster"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        mode: verbose
      register: result
    - name: "Show stdout"
      debug:
        var: result


- name: "PowerVC Backup"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Take a backup of the cluster"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        state: present
        preserve: 3
      register: result
    - name: "Show stdout"
      debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


# Execution
def construct_command(cluster_name, mode=None, preserve=None):
    """
    Construct the command based on the parameters

    :param str cluster_name: cluster name
    :param str mode: specifies the backup mode
    :param str preserve: specifies the number of backups to retain
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {
        r'PEXPECT_NEVER_MATCH': '',
    }
    command = None
    if cluster_name:
        command = f"powervc-opsmgr backup -c {cluster_name}"
        if mode == "silent":
            command += " --silent"
        elif mode == "verbose":
            command += " --verbose"
        if preserve is not None:
            command += f" -b {preserve}"
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            mode=dict(type='str', required=False, choices=[
                      'silent', 'verbose'], default='silent'),
            state=dict(type='str', required=False, choices=['present'], default='present'),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            preserve=dict(type='str', required=False, default=None),
            cluster=dict(type='str', required=True),
        )
    )
    mode = module.params['mode']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    preserve = module.params['preserve']
    cluster_name = module.params['cluster']
    output = None
    changed = False
    failed = True

    command, messages = construct_command(cluster_name, mode, preserve)
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

    if output:
        result['stdout_lines'] = output
        result['msg'] = "Backup operation completed successfully"
    else:
        result['warning'] = output
        result['msg'] = "Backup operation did not complete successfully"
    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
