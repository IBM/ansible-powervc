#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: ldap
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Display PowerVC LDAP configuration
description:
  - This module displays LDAP configuration for the PowerVC Controller.
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
  json_format:
    description:
      - When C(true), display LDAP configuration in JSON format.
    required: false
    type: bool
    default: false
'''

EXAMPLES = '''
- name: "Display LDAP config without JSON formatting"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Display without json formatting"
      ibm.powervc.cli.ldap:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        json_format: false
      register: result
    - name: "Show pvcldap output"
      debug:
        var: result.stdout_lines

- name: "Display LDAP config in JSON format"
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
    - name: "Show pvcldap output"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Always false — this module is read-only.
  returned: always
  type: bool
stdout:
  description: Raw command output.
  returned: always
  type: str
stdout_lines:
  description: Command output split into lines.
  returned: always
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd):
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd)
    rc, out = conn.run()
    # connection.run() always returns a list of strings
    lines = out if isinstance(out, list) else out.splitlines()
    stdout = "\n".join(lines)
    # pvcldap is read-only: return output even on non-zero rc so the caller
    # can surface whatever the command printed rather than raising a hard error
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

    # pvcldap exits rc=1 with "LDAP is NOT configured." when LDAP is not set up.
    # That is a valid read-only result, not a failure — always return the output.
    if json_format:
        rc, stdout, lines = run_cmd(
            module, login_host, login_user, login_password, "pvcldap --json")
        if rc != 0:
            # --json not supported on this PowerVC version OR LDAP not configured
            # — retry without flag so the plain message is surfaced
            rc, stdout, lines = run_cmd(
                module, login_host, login_user, login_password, "pvcldap")
            lines = clean_output(lines)
        # JSON output is returned verbatim — do not strip lines from a JSON object
    else:
        rc, stdout, lines = run_cmd(
            module, login_host, login_user, login_password, "pvcldap")
        lines = clean_output(lines)

    # Only fail for genuine command errors (e.g. binary not found, permission
    # denied).  rc=1 + "LDAP is NOT configured." is informational, not an error.
    if rc != 0 and not lines:
        module.fail_json(msg="pvcldap command failed", stderr=stdout, changed=False)

    stdout = "\n".join(lines)
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
            json_format=dict(type="bool", required=False, default=False),
        ),
        supports_check_mode=True
    )

    result = handle_ldap(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
