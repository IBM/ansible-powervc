#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: fdisk
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC Disk Partitions
description:
  - This module displays fdisk partitions for PowerVC
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
      - List the fdisk partitions
    required: true
    type: str
"""

EXAMPLE = """
---
- name: "Manage PowerVC Disk Partitions"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show the disk layout"
      ibm.powervc.cli.disk_layout:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "list"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

"""

from ansible.module_utils.basic import AnsibleModule
import traceback

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError


def run_remote_command(module, ip, user, password, state):
    state = "list"
    command = f"chpvc fdisk {state}"
    connection = Connection(module, ip, user, password, command)

    try:
        output = connection.run()
        return dict(
            changed=True,
            rc=0,
            stdout_lines=output,
            error=""
        )

    except CLIError as e:
        module.fail_json(
            msg=f"CLIError: {str(e)}",
            error=str(e),
            rc=1
        )
    except Exception as e:
        tb = traceback.format_exc()
        module.fail_json(
            msg=f"Unexpected exception: {str(e)}",
            error=tb,
            rc=1
        )


def main():
    module_args = dict(
        login_host=dict(type='str', required=True),
        login_user=dict(type='str', required=True),
        login_password=dict(type='str', required=True, no_log=True),
        state=dict(type='str', required=True),
    )

    module = AnsibleModule(argument_spec=module_args,
                           supports_check_mode=False)
    result = run_remote_command(
        module,
        module.params['login_host'],
        module.params['login_user'],
        module.params['login_password'],
        module.params['state']
    )

    module.exit_json(**result)


if __name__ == '__main__':
    main()
