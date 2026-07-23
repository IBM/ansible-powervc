#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: restore
author:
    - Yogita Garani (@yogita.garani1)
short_description: Restore the PowerVC cluster
description:
  - This module performs restore operation on the PowerVC Controller
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
      - State of restore, always present
    type: str
"""

EXAMPLES = """
---
- name: "Restore PowerVC cluster"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Restore cluster"
      ibm.powervc.cli.restore:
        state: present
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(cluster_name):
    """
    Construct the command based on the parameters

    :param str cluster_name: cluster name
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {
        r"Last successful backup at (.)*(\n)*(\s)*Do you want to continue restoring the backup? [Y/N]:(\s)*": 'y',
    }
    command = f'powervc-opsmgr restore -c {cluster_name}'
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            # Passing the IP as a parameter for now
            # Optimizations for single-node / multi-node can be made later
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True, no_log=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=True),
            state=dict(type='str', required=False, default='present'),

        )
    )
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster_name = module.params['cluster']
    output = None
    changed = False
    failed = True
    command, messages = construct_command(cluster_name)
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
        result['msg'] = "Restore operation completed successfully"
    else:
        result['warning'] = output
        result['msg'] = "Restore operation did not complete successfully"
    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
