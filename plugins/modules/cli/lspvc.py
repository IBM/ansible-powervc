#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: lspvc
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: List PowerVC information
description:
  - This module lists PowerVC information such as hypervisors, uvmid, and PowerVC version
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
  component:
    description:
      - Component to list
    required: true
    type: str
    choices: ['hypervisor', 'uvmid', 'powervc-version']
'''

EXAMPLES = '''
- name: List hypervisors on PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: List hypervisor information
      ibm.powervc.cli.lspvc:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: "hypervisor"
      register: result

    - name: Display hypervisor output
      debug:
        var: result.stdout_lines


- name: List UVMIDs on PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: List uvmid information
      ibm.powervc.cli.lspvc:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: "uvmid"
      register: result

    - name: Display uvmid output
      debug:
        var: result.stdout_lines


- name: List PowerVC version
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: List PowerVC version information
      ibm.powervc.cli.lspvc:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: "powervc-version"
      register: result

    - name: Display version output
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether any changes were made (always false for read-only list operations)
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


def run_cmd(module, host, username, password, cmd):
    conn = Connection(module, host, username, password, command=cmd)
    rc, out = conn.run()
    if rc != 0:
        module.fail_json(msg=f"Command failed: {cmd}", stderr=out)

    if isinstance(out, list):
        return "\n".join(out), out

    return out, out


def result_ok(lines, changed=False):
    return {
        "changed": changed,
        "stdout": "\n".join(lines),
        "stdout_lines": lines
    }


def clean_lspvc_output(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        cleaned.append(line)
    return cleaned


def handle_list(module, host, username, password, component):
    valid_components = ["hypervisor", "uvmid", "powervc-version"]

    if component not in valid_components:
        module.fail_json(
            msg=f"Invalid component '{component}'. "
                f"Valid options are: {', '.join(valid_components)}"
        )

    command = f"lspvc list-{component}"
    _, lines = run_cmd(module, host, username, password, command)
    cleaned = clean_lspvc_output(lines)

    if not cleaned:
        return result_ok(["No output returned"])

    return result_ok(cleaned, changed=False)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            component=dict(
                type="str",
                required=True,
                choices=["hypervisor", "uvmid", "powervc-version"]
            )
        ),
        supports_check_mode=True
    )

    host = module.params["login_host"]
    username = module.params["login_user"]
    password = module.params["login_password"]
    component = module.params["component"]

    result = handle_list(module, host, username, password, component)

    module.exit_json(**result)


if __name__ == "__main__":
    main()
