#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: config_policy
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC cluster policy configuration
description:
  - This module manages the policy configuration of a PowerVC cluster via
    C(powervc-opsmgr config policy) over SSH.
  - C(state=show) reads and returns the current policy configuration without
    making any changes. Always returns C(changed=False).
  - C(state=present) sets the cluster policy to C(restricted) or C(ppc).
    This operation is B(idempotent) — the module reads the current policy first
    (C(powervc-opsmgr config policy -c <cluster> -s)) and skips the set command
    if the desired policy is already active, returning C(changed=False).
  - C(--check) mode is supported. For C(state=present) the module reads current
    state and reports C(changed=False) if already compliant, C(changed=True) if
    a change would be made — without executing the set command.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller.
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot)).
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user.
    required: true
    type: str
    no_log: true
  cluster:
    description:
      - Cluster name.
    required: true
    type: str
  state:
    description:
      - C(show) — read and return the current policy configuration (read-only,
        always C(changed=False)).
      - C(present) — set the cluster policy. Requires C(policy). Idempotent —
        skips execution if the policy is already set to the desired value.
    type: str
    choices: ['present', 'show']
    default: show
  policy:
    description:
      - Policy type to apply. Required when C(state=present).
      - C(restricted) — apply the Restricted Policy (C(-r) flag).
      - C(ppc) — apply the PowerVC Private Cloud Policy (C(-p) flag).
    type: str
    choices: ['restricted', 'ppc']
    required: false
  verbose:
    description:
      - Enable verbose output from C(powervc-opsmgr) (C(-v) flag).
    type: bool
    default: false
'''

EXAMPLES = '''
- name: "Show current policy configuration"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Read current policy"
      ibm.powervc.cli.config_policy:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        state: show
      register: result

    - name: "Display current policy"
      debug:
        var: result.stdout_lines


- name: "Set cluster policy"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Apply policy (idempotent — skips if already set)"
      ibm.powervc.cli.config_policy:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        state: present
        policy: "{{ policy }}"
      register: result

    - name: "Show result"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: >
    C(false) for C(state=show), on failure, or when the desired policy is
    already active (idempotent). C(true) when the policy was changed.
  returned: always
  type: bool
rc:
  description: Return code from the remote command.
  returned: always
  type: int
stdout_lines:
  description: Command output split into lines.
  returned: always
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

import re as _re

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule

_ANSI_RE = _re.compile(r'\x1b(?:\[[0-9;]*[A-Za-z]|\][^\x07\x1b]*[\x07\x1b]|c)')


def _strip_ansi(s):
    return _ANSI_RE.sub('', s)


def _read_current_policy(module, host_ip, user, password, cluster):
    '''Read current policy via ``powervc-opsmgr config policy -c <cluster> -s``.

    Returns the lowercased policy string (e.g. ``"restricted"``, ``"ppc"``)
    extracted from the output, or None if the read fails or cannot be parsed —
    callers skip idempotency rather than aborting.
    '''
    cmd = f"powervc-opsmgr config policy -c {cluster} -s"
    connection = Connection(module, host_ip, user, password,
                            command=cmd, messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None

    if int(rc) != 0:
        return None

    lines = output if isinstance(output, list) else str(output).splitlines()
    for line in lines:
        line = _strip_ansi(line).strip().lower()
        if 'restricted' in line:
            return 'restricted'
        if 'ppc' in line or 'private cloud' in line:
            return 'ppc'
    return None


def _run_command(module, host_ip, user, password, command):
    '''Run command via SSH. Returns (rc, lines). Raises CLIError on failure.'''
    connection = Connection(module, host_ip, user, password,
                            command=command, messages={})
    try:
        rc, output = connection.run()
    except (CLIError, Exception) as e:
        module.fail_json(changed=False, rc=1, msg=str(e))
    return rc, output if isinstance(output, list) else str(output).splitlines()


def run_config_policy(module):
    '''Main logic — read params, check idempotency, execute if needed.'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster = module.params['cluster']
    state = module.params['state']
    policy = module.params.get('policy')
    verbose = module.params.get('verbose', False)

    # Validate: policy is required for state=present
    if state == 'present' and not policy:
        module.fail_json(
            changed=False, rc=1,
            msg="'policy' is required when state='present'"
        )

    # ── state=show — read-only, never changes anything ──
    if state == 'show':
        cmd = f"powervc-opsmgr config policy -c {cluster} -s"
        if verbose:
            cmd += " -v"
        rc, lines = _run_command(module, host_ip, user, password, cmd)
        if int(rc) != 0:
            stderr = "\n".join(lines)
            module.fail_json(changed=False, rc=int(rc),
                             msg=f"Failed to read policy: {stderr}")
        module.exit_json(
            changed=False, rc=0,
            stdout_lines=lines,
            msg="Policy configuration retrieved successfully"
        )

    # ── state=present — idempotency check before mutating ──
    current_policy = _read_current_policy(module, host_ip, user, password, cluster)
    if current_policy is not None and current_policy == policy.lower():
        module.exit_json(
            changed=False, rc=0,
            stdout_lines=[f"Policy already set to '{policy}' — no change required"],
            msg=f"Policy already set to '{policy}' — no change required"
        )

    # Build the set command
    cmd = f"powervc-opsmgr config policy -c {cluster}"
    if verbose:
        cmd += " -v"
    if policy == 'restricted':
        cmd += " -r"
    elif policy == 'ppc':
        cmd += " -p"

    # check_mode: idempotency pre-read already ran — reaching here means a
    # real change would be made.
    if module.check_mode:
        module.exit_json(
            changed=True, rc=0,
            stdout_lines=[],
            msg=f"[CHECK MODE] Would run: {cmd}"
        )

    rc, lines = _run_command(module, host_ip, user, password, cmd)
    if int(rc) != 0:
        stderr = "\n".join(lines)
        module.fail_json(changed=False, rc=int(rc),
                         msg=f"Policy configuration failed: {stderr}")

    module.exit_json(
        changed=True, rc=0,
        stdout_lines=lines if lines else [f"Policy set to '{policy}' successfully"],
        msg=f"Policy set to '{policy}' successfully"
    )


def main():
    '''Main execution'''
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=True),
            state=dict(type='str', default='show',
                       choices=['present', 'show']),
            policy=dict(type='str', required=False,
                        choices=['restricted', 'ppc']),
            verbose=dict(type='bool', required=False, default=False),
        ),
        required_if=[
            ('state', 'present', ['policy']),
        ],
        supports_check_mode=True
    )

    run_config_policy(module)


if __name__ == '__main__':
    main()
