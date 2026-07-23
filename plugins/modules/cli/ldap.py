#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: ldap
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Displays PowerVC LDAP Configuration
description:
  - This module displays LDAP configurations for PowerVC
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
  json_format:
    description:
      - Displays LDAP configurations in json format
    required: true
    type: bool
"""

EXAMPLE = """
---
- name: Check and display LDAP config status on a PowerVC node.
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

    - name: "Display without json formatting"
      ibm.powervc.cli.ldap:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        json_format: false
      register: result

    - name: Show pvcldap output
      debug:
        var: result.stdout_lines

---
- name: Check and display LDAP config status on a PowerVC node.
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Display in json format"
      ibm.powervc.cli.ldap:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        json_format: true
      register: result

    - name: Show pvcldap output
      debug:
        var: result.stdout_lines

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd):
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd)
    rc, out = conn.run()
    if isinstance(out, list):
        stdout = "\n".join(out)
        lines = out
    else:
        stdout = out
        lines = out.splitlines()
    return rc, stdout, lines


def clean_output(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("+"):
            continue
        if "End of" in line:
            continue
        cleaned.append(line)
    return cleaned


def handle_ldap(module):
    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    json_format = module.params["json_format"]

    if json_format:
        cmd = "pvcldap --json"
    else:
        cmd = "pvcldap --show"

    rc, stdout, lines = run_cmd(
        module, login_host, login_user, login_password, cmd)

    return {
        "changed": False,
        "stdout": stdout,
        "stdout_lines": lines
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            json_format=dict(type="bool", required=True),
        ),
        supports_check_mode=False
    )

    result = handle_ldap(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
