#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: configure
author:
    - Yogita Garani (@yogita.garani1)
short_description: Configure PowerVC
description:
  - This module performs a configure operation on the PowerVC Controller
    using C(powervc-opsmgr configure).
  - B(Idempotency) — when the cluster is already configured,
    C(powervc-opsmgr configure) exits with C(rc=1) and prints
    C(IBM PowerVC Configuration has already gone through) to stderr.
    The module detects this phrase (and related variants such as
    C(already configured), C(no changes), C(use --force/-f option)) in
    the combined output B(before) checking the exit code, and returns
    C(changed=False) instead of failing. Re-running the module against an
    already-configured cluster is therefore safe.
  - To reconfigure a cluster that was already configured, set C(force=true).
  - When C(validate=True) (C(-pv) flag), C(powervc-opsmgr configure) prompts
    interactively for an OpenStack health-check username and password.
    Supply C(health_user) and C(health_password) so the module can answer
    these prompts non-interactively. Both are required when C(validate=True).
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
      - Cluster name to configure
    required: true
    type: str
  validate:
    description:
      - Validate after configure (C(-pv) flag). When C(true), the command
        prompts for an OpenStack health-check username and password —
        supply C(health_user) and C(health_password) to answer them.
    type: bool
  health_user:
    description:
      - Username for checking OpenStack services health status.
        Passed to the C(Enter the username for checking openstack services
        health status) prompt. Required when C(validate=true).
    required: false
    type: str
  health_password:
    description:
      - Password for C(health_user). Passed to the C(Enter password for)
        interactive prompt. Required when C(validate=true).
    required: false
    type: str
    no_log: true
  force:
    description:
      - Force configure PowerVC (C(-f) flag)
    type: bool
  verbose:
    description:
      - Configure PowerVC with verbose logging (C(-v) flag)
    type: bool
'''

EXAMPLES = '''
- name: Configure PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Run configure on the cluster
      ibm.powervc.cli.configure:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: Display configure output
      debug:
        var: result


- name: Configure PowerVC with validation
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Run configure and validate
      ibm.powervc.cli.configure:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        validate: true
        health_user: "{{ health_user }}"
        health_password: "{{ health_password }}"
      register: result

    - name: Display validate configure output
      debug:
        var: result.stdout_lines


- name: Configure PowerVC in verbose mode
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Run configure with verbose logging
      ibm.powervc.cli.configure:
        verbose: true
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: Display verbose configure output
      debug:
        var: result


- name: Force configure PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Run force configure
      ibm.powervc.cli.configure:
        force: true
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: Display force configure output
      debug:
        var: result
'''

RETURN = '''
changed:
  description: >
    Whether the configure operation was performed.
    C(false) when the cluster was already configured (no changes made).
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
msg:
  description: Human-readable status message
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def build_command(cluster_name, validate=None, force=None, verbose=None):
    '''Construct the powervc-opsmgr configure command'''
    if force:
        return f"powervc-opsmgr configure -c {cluster_name} -f"
    if verbose:
        return f"powervc-opsmgr configure -c {cluster_name} -v"
    if validate:
        return f"powervc-opsmgr configure -c {cluster_name} -pv"
    return f"powervc-opsmgr configure -c {cluster_name}"


def build_messages(validate=None, health_user=None, health_password=None):
    '''Return the interactive-prompt messages dict for Connection.

    When validate=True the CLI asks:
      "Enter the username for checking openstack services health status:"
      "Enter password for <username>:"
    Both are answered here so the command runs non-interactively.
    '''
    if not validate:
        return {}
    return {
        r"Enter the username for checking openstack services health status\s*:\s*": health_user or "",
        r"Enter password for .*:\s*": health_password or "",
    }


# Phrases in stdout OR stderr that indicate the cluster is already configured.
# powervc-opsmgr configure exits rc=1 and writes to stderr when already done,
# so we must check combined output before deciding to fail.
_ALREADY_CONFIGURED_PHRASES = (
    "already configured",
    "no changes",
    "has already gone through",    # "IBM PowerVC Configuration has already gone through"
    "use --force/-f option",        # "Use --force/-f option to rerun"
)


def run_configure(module):
    '''Execute the configure command on the PowerVC controller'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster_name = module.params['cluster']
    validate = module.params['validate']
    verbose = module.params['verbose']
    force = module.params['force']
    health_user = module.params.get('health_user')
    health_password = module.params.get('health_password')

    command = build_command(cluster_name, validate, force, verbose)
    messages = build_messages(validate, health_user, health_password)

    # check_mode: report what would run without touching the system
    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would configure cluster {cluster_name}"
        )

    connection = Connection(module, host_ip, user, password,
                            command=command, messages=messages)

    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    lines = output if isinstance(output, list) else [str(output)]
    stdout = "\n".join(lines)
    lower = stdout.lower()

    # Idempotency check — must run BEFORE the rc != 0 guard because
    # powervc-opsmgr configure exits rc=1 with the "already gone through"
    # message on stderr when the cluster is already configured.
    already = any(phrase in lower for phrase in _ALREADY_CONFIGURED_PHRASES)
    if already:
        module.exit_json(
            changed=False,
            stdout=stdout,
            stdout_lines=lines,
            msg="Cluster is already configured — no changes made"
        )

    if int(rc) != 0:
        module.fail_json(
            msg="Configure operation did not complete successfully",
            stderr=stdout,
            rc=int(rc)
        )

    module.exit_json(
        changed=True,
        stdout=stdout,
        stdout_lines=lines,
        msg="Configure operation completed successfully"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=True),
            validate=dict(type='bool', required=False),
            health_user=dict(type='str', required=False),
            health_password=dict(type='str', required=False, no_log=True),
            verbose=dict(type='bool', required=False),
            force=dict(type='bool', required=False),
        ),
        required_if=[
            ('validate', True, ['health_user', 'health_password']),
        ],
        supports_check_mode=True
    )

    run_configure(module)


if __name__ == '__main__':
    main()
