#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: restore
author:
    - Yogita Garani (@yogita.garani1)
short_description: Restore the PowerVC cluster
description:
  - This module performs a restore operation on the PowerVC Controller
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
  cluster:
    description:
      - Cluster name to restore
    required: true
    type: str
'''

EXAMPLES = '''
- name: Restore PowerVC cluster
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Restore the named cluster
      ibm.powervc.cli.restore:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: Display restore output
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the restore operation was performed
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


def run_restore(module):
    '''Execute the restore command on the PowerVC controller'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster_name = module.params['cluster']

    # check_mode: restore is destructive — report what would run without acting
    if module.check_mode:
        module.exit_json(
            changed=True,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would restore cluster {cluster_name}"
        )

    command = f'powervc-opsmgr restore -c {cluster_name}'
    messages = {
        r"Last successful backup at (.)*(\n)*(\s)*Do you want to continue restoring the backup? [Y/N]:(\s)*": 'y',
    }

    connection = Connection(module, host_ip, user, password,
                            command=command, messages=messages)

    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(msg="Restore operation did not complete successfully", stderr=stderr_msg)

    lines = output if isinstance(output, list) else [str(output)]

    module.exit_json(
        changed=True,
        stdout="\n".join(lines),
        stdout_lines=lines,
        msg="Restore operation completed successfully"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=True),
        ),
        supports_check_mode=True
    )

    run_restore(module)


if __name__ == '__main__':
    main()
