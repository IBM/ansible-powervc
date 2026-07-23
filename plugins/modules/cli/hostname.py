#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: hostname
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage Hostname
description:
  - This module displays and modifies hostname
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
  state:
    description:
      - Display or modify hostname
    required: true
    type: str
  new_hostname:
    description:
      - New hostname to be set
    type: str
"""

EXAMPLE = """
---
- name: "Manage PowerVC Hostname"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Modify hostname"
      ibm.powervc.cli.hostname:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "modify"
        new_hostname: "{{ value }}"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

---
- name: "Manage PowerVC Hostname"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show the hostname"
      ibm.powervc.cli.hostname:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd):
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd)
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


def clean_hostname_output(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line:
            continue
        if line.startswith("+"):
            continue
        if "End of chpvc" in line:
            continue
        cleaned.append(line)
    return cleaned


def handle_show(module, login_host, login_user, login_password):
    _, lines = run_cmd(module, login_host, login_user,
                       login_password, "chpvc hostname show")
    cleaned = clean_hostname_output(lines)

    if not cleaned:
        return result_ok(["No hostname returned"])

    return result_ok([cleaned[0]])


def handle_modify(module, login_host, login_user, login_password, new_hostname):
    _, lines = run_cmd(module, login_host, login_user,
                       login_password, "chpvc hostname show")
    cleaned = clean_hostname_output(lines)

    if not cleaned:
        module.fail_json(msg="Unable to determine current hostname")

    current_hostname = cleaned[0].strip()

    if current_hostname == new_hostname:
        return result_ok(
            [f"Hostname already set to {current_hostname}"],
            changed=False
        )

    run_cmd(
        module,
        login_host,
        login_user,
        login_password,
        f"chpvc hostname modify {new_hostname}"
    )

    return result_ok(
        [f"Hostname updated to {new_hostname}"],
        changed=True
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=["show", "modify"]),
            new_hostname=dict(type="str")
        ),
        required_if=[
            ("state", "modify", ["new_hostname"])
        ],
        supports_check_mode=False
    )

    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    state = module.params["state"]
    new_hostname = module.params.get("new_hostname")

    if state == "show":
        result = handle_show(module, login_host, login_user, login_password)

    elif state == "modify":
        result = handle_modify(
            module, login_host, login_user, login_password, new_hostname)

    else:
        module.fail_json(msg="Invalid state")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
