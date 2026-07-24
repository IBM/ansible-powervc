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
  - This module performs a configure operation on the PowerVC Controller.
  - If the configure output indicates the cluster is already configured
    (contains C(already configured) or C(no changes)), the module reports
    C(changed=False) so playbook runs remain idempotent.
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
      - Validate after configure (C(-pv) flag)
    type: bool
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
        validate: true
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: Display validate configure output
      debug:
        var: result


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


_ALREADY_CONFIGURED_PHRASES = ("already configured", "no changes")


def run_configure(module):
    '''Execute the configure command on the PowerVC controller'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster_name = module.params['cluster']
    validate = module.params['validate']
    verbose = module.params['verbose']
    force = module.params['force']

    command = build_command(cluster_name, validate, force, verbose)

    # check_mode: report what would run without touching the system
    if module.check_mode:
        module.exit_json(
            changed=False,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would configure cluster {cluster_name}"
        )

    connection = Connection(module, host_ip, user, password, command=command)

    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(msg="Configure operation did not complete successfully", stderr=stderr_msg)

    lines = output if isinstance(output, list) else [str(output)]
    stdout = "\n".join(lines)

    # Idempotency: if the cluster was already configured, report no change
    lower = stdout.lower()
    already = any(phrase in lower for phrase in _ALREADY_CONFIGURED_PHRASES)

    module.exit_json(
        changed=not already,
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
            verbose=dict(type='bool', required=False),
            force=dict(type='bool', required=False),
        ),
        supports_check_mode=True
    )

    run_configure(module)


if __name__ == '__main__':
    main()
