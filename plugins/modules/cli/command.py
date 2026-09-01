#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: command
author:
    - Yogita Garani (@yogita.garani1)
short_description: Execute a CLI command on the PowerVC Controller
description:
  - This module executes an arbitrary CLI command on the PowerVC Controller
    over SSH. Optional interactive prompt-response pairs can be supplied via
    the C(messages) parameter for commands that require user input.
  - By default C(changed=true) is returned on success because the module
    cannot inspect remote state. Use C(creates) or C(removes) to make the
    result idempotent — the module skips execution and returns C(changed=false)
    when the named remote path already exists (C(creates)) or does not exist
    (C(removes)).
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
    no_log: true
  command:
    description:
      - The CLI command to execute on the PowerVC Controller.
    required: true
    type: str
  messages:
    description:
      - A dictionary of expected prompt patterns (regex) mapped to the
        response string to send. Used for interactive commands.
        If omitted or empty the command runs non-interactively.
    required: false
    type: dict
    default: {}
  creates:
    description:
      - A remote path. If this path B(already exists) on the PowerVC
        Controller the command is B(skipped) and C(changed=false) is
        returned. Use when a command creates a resource that should not
        be recreated on subsequent runs.
    required: false
    type: str
  removes:
    description:
      - A remote path. If this path B(does not exist) on the PowerVC
        Controller the command is B(skipped) and C(changed=false) is
        returned. Use when a command removes a resource and should not
        run again after the resource is gone.
    required: false
    type: str
'''

EXAMPLES = '''
- name: "Remote command execution - simple"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run a command on the PowerVC Controller"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "{{ command }}"
      register: result
    - name: "Show stdout"
      debug:
        var: result.stdout_lines

- name: "Remote command execution - interactive"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run a command with interactive prompt responses"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "powervc-opsmgr restore -c siva1234"
        messages:
          'Do you want to continue restoring the backup[?] [Y/N]:': 'y'
      register: result
    - name: "Show stdout"
      debug:
        var: result.stdout_lines

- name: "Idempotent command using creates"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run only if /powervchome/myfile does not already exist"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "touch /powervchome/myfile"
        creates: "/powervchome/myfile"
      register: result
    - name: "Show stdout"
      debug:
        var: result.stdout_lines

- name: "Idempotent command using removes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run only while /tmp/lockfile still exists"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        command: "rm -f /tmp/lockfile"
        removes: "/tmp/lockfile"
      register: result
    - name: "Show stdout"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: >
    True when the command ran and succeeded. False when skipped due to
    C(creates)/C(removes) condition or when run in check_mode.
  returned: always
  type: bool
rc:
  description: Return code from the executed command.
  returned: when command was executed
  type: int
stdout_lines:
  description: Output from the command split into a list of lines.
  returned: when command was executed
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
skipped_reason:
  description: Explanation of why the command was skipped (creates/removes).
  returned: when skipped
  type: str
'''

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


def _remote_path_exists(module, host_ip, user, password, path):
    '''Return True if path exists on the remote host (uses test -e).'''
    conn = Connection(module, host_ip, user, password,
                      command=f'test -e {path}')
    rc, _ = conn.run()
    return rc == 0


def run_command(module):
    '''
    Execute the CLI command on the PowerVC Controller.

    :param module: AnsibleModule instance
    '''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    command = module.params['command'].strip()
    messages = module.params['messages'] or {}
    creates = module.params.get('creates')
    removes = module.params.get('removes')

    if not command:
        module.fail_json(changed=False, msg="'command' parameter must not be empty")

    # check_mode: report what would run without executing
    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"[CHECK MODE] Would run: {command}"
        )

    # creates: skip if the remote path already exists
    if creates:
        if _remote_path_exists(module, host_ip, user, password, creates):
            module.exit_json(
                changed=False,
                msg=f"Skipped — '{creates}' already exists",
                skipped_reason=f"creates path '{creates}' already exists"
            )

    # removes: skip if the remote path no longer exists
    if removes:
        if not _remote_path_exists(module, host_ip, user, password, removes):
            module.exit_json(
                changed=False,
                msg=f"Skipped — '{removes}' does not exist",
                skipped_reason=f"removes path '{removes}' does not exist"
            )

    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        module.fail_json(
            msg=f"Command failed with rc={rc}",
            rc=int(rc),
            stderr=output,
            changed=False
        )

    if not output:
        module.warn("Command returned no output")

    module.exit_json(
        changed=True,
        rc=int(rc),
        stdout_lines=output if output else [],
        msg="Operation completed successfully"
    )


def main():
    '''
    Main execution
    '''
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            command=dict(type='str', required=True),
            messages=dict(type='dict', required=False, default={}),
            creates=dict(type='str', required=False, default=None),
            removes=dict(type='str', required=False, default=None),
        ),
        supports_check_mode=True
    )

    run_command(module)


if __name__ == '__main__':
    main()
