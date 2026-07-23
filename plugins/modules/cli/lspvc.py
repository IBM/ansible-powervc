#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: lspvc
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: List PowerVC information
description:
  - This module lists PowerVC information such as hypervisors, uvmid, and PowerVC version
options:
  host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  username:
    description:
      - SSH User (pvcroot)
    required: true
    type: str
  password:
    description:
      - Password for the ssh user
    required: true
    type: str
  state:
    description:
      - Action to perform (present to list information)
    required: true
    type: str
    choices: ['present']
  component:
    description:
      - Component to list (hypervisor, uvmid, or powervc-version)
    required: true
    type: str
    choices: ['hypervisor', 'uvmid', 'powervc-version']
"""

EXAMPLE = """
---
- name: "Run lspvc command on PowerVC host"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "List hypervisor"
      ibm.powervc.cli.lspvc:
        host: "{{ ipaddress }}"
        username: "{{ pvc_user }}"
        password: "{{ pvcroot_password }}"
        state: "present"
        component: "hypervisor"
      register: result

    - name: "Display command output"
      debug:
        var: result.stdout_lines

---
- name: "Run lspvc command on PowerVC host"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "List uvmid"
      ibm.powervc.cli.lspvc:
        host: "{{ ipaddress }}"
        username: "{{ pvc_user }}"
        password: "{{ pvcroot_password }}"
        state: "present"
        component: "uvmid"
      register: result

    - name: "Display command output"
      debug:
        var: result.stdout_lines

---
- name: "Run lspvc command on PowerVC host"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "List PowerVC version"
      ibm.powervc.cli.lspvc:
        host: "{{ ipaddress }}"
        username: "{{ pvc_user }}"
        password: "{{ pvcroot_password }}"
        state: "present"
        component: "powervc-version"
      register: result

    - name: "Display command output"
      debug:
        var: result.stdout_lines

"""
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


def handle_present(module, host, username, password, component):
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
            host=dict(type="str", required=True),
            username=dict(type="str", required=True),
            password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=["present"]),
            component=dict(
                type="str",
                required=True,
                choices=["hypervisor", "uvmid", "powervc-version"]
            )
        ),
        supports_check_mode=False
    )

    host = module.params["host"]
    username = module.params["username"]
    password = module.params["password"]
    state = module.params["state"]
    component = module.params["component"]

    if state == "present":
        result = handle_present(module, host, username, password, component)
    else:
        module.fail_json(msg="Invalid state")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
