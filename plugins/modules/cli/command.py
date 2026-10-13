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
  - For commands that require OpenStack credentials (e.g. C(openstack) CLI),
    supply the C(os_username), C(os_password), and optionally the other C(os_*)
    parameters instead of building the C(env) dict manually. The module will
    construct the correct C(OS_AUTH_URL), C(OS_USERNAME), C(OS_PASSWORD),
    C(OS_PROJECT_NAME), C(OS_USER_DOMAIN_NAME), C(OS_PROJECT_DOMAIN_NAME),
    C(OS_IDENTITY_API_VERSION), and C(PYTHONHTTPSVERIFY) environment variables
    automatically. Any key supplied explicitly in C(env) takes precedence over
    the auto-generated value.
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
  env:
    description:
      - A dictionary of environment variables to set on the remote SSH channel
        before executing the command. Variables are injected inline as
        C(KEY='value') prefixes on the command string so they are guaranteed
        to reach the executed process regardless of C(sshd) C(AcceptEnv) or
        C(PermitUserEnvironment) settings and bypass any shell restrictions
        (e.g. C(rbash)).
      - Use this for any env vars the remote command requires. For OpenStack
        credentials specifically, prefer the dedicated C(os_username) /
        C(os_password) / C(os_auth_url) parameters — the module will build the
        full OpenStack env dict automatically.
      - Any key supplied here overrides the same key auto-generated from the
        C(os_*) parameters.
    required: false
    type: dict
    default: {}
  os_username:
    description:
      - OpenStack username for authenticating C(openstack) CLI calls.
        Typically C(servicebroker) or C(pvcroot).
      - When supplied together with C(os_password), the module automatically
        builds the full set of C(OS_*) environment variables so you do not
        have to construct the C(env) dict manually.
    required: false
    type: str
  os_password:
    description:
      - Password for C(os_username).
      - Required when C(os_username) is set. Injected via the environment so
        it never appears on the command line.
    required: false
    type: str
    no_log: true
  os_auth_url:
    description:
      - Full Keystone endpoint, e.g. C(https://9.47.64.53:5000/v3).
      - When omitted, auto-derived as C(https://<login_host>:5000/v3).
    required: false
    type: str
  os_project:
    description:
      - OpenStack project scope for the authentication token.
      - Use C(service) for C(servicebroker) (the default) or the target project
        name for C(pvcroot).
    required: false
    type: str
    default: service
  os_user_domain_name:
    description:
      - Keystone user domain name.
    required: false
    type: str
    default: Default
  os_project_domain_name:
    description:
      - Keystone project domain name.
    required: false
    type: str
    default: Default
  os_identity_api_version:
    description:
      - Keystone API version.
    required: false
    type: str
    default: '3'
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

- name: "Run an openstack CLI command - using os_* convenience params"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List OpenStack role assignments (OS env auto-built)"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        command: "openstack role assignment list --project 'ibm-default' --insecure"
      register: result
    - name: "Show stdout"
      debug:
        var: result.stdout_lines

- name: "Run an openstack CLI command - using raw env dict"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List OpenStack role assignments (env dict supplied manually)"
      ibm.powervc.cli.command:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        env:
          OS_AUTH_URL: "https://{{ ipaddress }}:5000/v3"
          OS_USERNAME: "{{ os_username }}"
          OS_PASSWORD: "{{ os_password }}"
          OS_PROJECT_NAME: "service"
          OS_USER_DOMAIN_NAME: "Default"
          OS_PROJECT_DOMAIN_NAME: "Default"
          OS_IDENTITY_API_VERSION: "3"
          PYTHONHTTPSVERIFY: "0"
        command: "openstack role assignment list --project 'ibm-default' --insecure"
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

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection, build_os_env
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
    env = dict(module.params.get('env') or {})
    creates = module.params.get('creates')
    removes = module.params.get('removes')

    os_username = module.params.get('os_username')
    os_password = module.params.get('os_password')

    # When os_username/os_password are supplied, auto-build the OpenStack env
    # dict and merge it under any explicitly supplied env keys (explicit wins).
    if os_username and os_password:
        os_auth_url = (module.params.get('os_auth_url')
                       or f"https://{host_ip}:5000/v3")
        auto_env = build_os_env(
            os_auth_url=os_auth_url,
            os_username=os_username,
            os_password=os_password,
            os_project=module.params.get('os_project') or 'service',
            os_user_domain_name=module.params.get('os_user_domain_name') or 'Default',
            os_project_domain_name=module.params.get('os_project_domain_name') or 'Default',
            os_identity_api_version=module.params.get('os_identity_api_version') or '3',
        )
        # auto_env provides defaults; explicit env keys override them.
        merged = {**auto_env, **env}
        env = merged

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
                            password, command=command, messages=messages, env=env)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        module.fail_json(
            msg=f"Command failed with rc={rc}",
            rc=int(rc),
            stderr='\n'.join(output) if isinstance(output, list) else output,
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
            env=dict(type='dict', required=False, default={}),
            os_username=dict(type='str', required=False),
            os_password=dict(type='str', required=False, no_log=True),
            os_auth_url=dict(type='str', required=False, default=None),
            os_project=dict(type='str', required=False, default='service'),
            os_user_domain_name=dict(type='str', required=False, default='Default'),
            os_project_domain_name=dict(type='str', required=False, default='Default'),
            os_identity_api_version=dict(type='str', required=False, default='3'),
            command=dict(type='str', required=True),
            messages=dict(type='dict', required=False, default={}),
            creates=dict(type='str', required=False, default=None),
            removes=dict(type='str', required=False, default=None),
        ),
        required_together=[['os_username', 'os_password']],
        supports_check_mode=True
    )

    run_command(module)


if __name__ == '__main__':
    main()
