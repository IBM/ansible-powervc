#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: backup
author:
    - Yogita Garani (@yogita.garani1)
short_description: Take a backup on PowerVC
description:
  - This module performs a backup operation on the PowerVC Controller.
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
  preserve:
    description:
      - Number of previous backups to preserve during cleanup.
    type: int
  mode:
    description:
      - Mode of logging. Use C(silent) to suppress output or C(verbose) for
        detailed output.
    type: str
    choices: ['silent', 'verbose']
    default: silent
'''

EXAMPLES = '''
- name: "PowerVC Backup - silent mode"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Take a backup of the cluster (silent)"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        mode: "silent"
      register: result
    - name: "Show output"
      debug:
        var: result

- name: "PowerVC Backup - verbose mode"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Take a backup of the cluster (verbose)"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        mode: "verbose"
      register: result
    - name: "Show output"
      debug:
        var: result

- name: "PowerVC Backup - with preserve count"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Take a backup and keep last 3"
      ibm.powervc.cli.backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        preserve: 3
      register: result
    - name: "Show output"
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the backup operation ran and succeeded.
  returned: always
  type: bool
rc:
  description: Return code from the backup command.
  returned: always
  type: int
stdout_lines:
  description: Output from the backup command split into lines.
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


def construct_command(cluster_name, mode=None, preserve=None):
    '''
    Construct the backup command from the given parameters.

    :param str cluster_name: cluster name
    :param str mode: backup mode (silent or verbose)
    :param int preserve: number of backups to retain
    :return str|None command: constructed command string
    '''
    command = None
    if cluster_name:
        command = f"powervc-opsmgr backup -c {cluster_name}"
        if mode == "silent":
            command += " --silent"
        elif mode == "verbose":
            command += " --verbose"
        if preserve is not None:
            command += f" -b {int(preserve)}"
    return command


def run_backup(module):
    '''
    Execute the backup command on the PowerVC Controller.

    :param module: AnsibleModule instance
    '''
    mode = module.params['mode']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    preserve = module.params['preserve']
    cluster_name = module.params['cluster']

    command = construct_command(cluster_name, mode, preserve)

    if command is None:
        module.fail_json(
            changed=False,
            msg="Could not construct backup command — check the 'cluster' parameter"
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"[CHECK MODE] Would run backup for cluster '{cluster_name}': {command}"
        )

    connection = Connection(module, host_ip, user, password, command=command)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    # F1: non-zero exit code is a genuine failure — use fail_json so Ansible
    # marks the task FAILED and triggers block/rescue and failed_when handlers.
    if int(rc) != 0:
        module.fail_json(
            msg="Backup operation failed",
            rc=int(rc),
            stderr=output,
            changed=False
        )

    # F2: warn (not silently drop) when the command produced no output.
    if not output:
        module.warn("Backup command succeeded but returned no output")

    # F4: build the result once from final values — no stale pre-initialisation.
    module.exit_json(
        changed=True,
        failed=False,
        rc=int(rc),
        stdout_lines=output if output else [],
        msg="Backup operation completed successfully"
    )


def main():
    '''
    Main execution
    '''
    # F8: AnsibleModule instantiated in main() and passed to the handler,
    # matching collection convention and enabling unit testing.
    module = AnsibleModule(
        argument_spec=dict(
            # F7: state removed — it was always 'present' and never branched on
            mode=dict(type='str', required=False, choices=[
                      'silent', 'verbose'], default='silent'),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            # F6: preserve declared as int to match DOCUMENTATION and for safe
            # embedding in the shell command
            preserve=dict(type='int', required=False, default=None),
            cluster=dict(type='str', required=True),
        ),
        # F5: write path is guarded by module.check_mode inside run_backup()
        supports_check_mode=True
    )
    run_backup(module)


if __name__ == '__main__':
    main()
