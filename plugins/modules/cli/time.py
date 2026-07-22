#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: time
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Displays and sets time, shows time settings and properties
description:
  - This module displays and sets time, settings and properties
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
      - State of time operations
    required: true
    type: str
  action:
    description:
      - Actions like settings and properties
    type: str
  value:
    description:
      - Time value to be set
    type: str
"""

EXAMPLE = """
---
- name: "Manage PowerVC time commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show settings"
      ibm.powervc.cli.time:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        action: "{{ timezone_action }}"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

---
- name: "Manage PowerVC time commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show properties"
      ibm.powervc.cli.time:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        action: "{{ timezone_action }}"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Manage PowerVC time commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Set time"
      ibm.powervc.cli.time:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "present"
        value: "{{ timezone_value }}"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Manage PowerVC time commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show current time"
      ibm.powervc.cli.time:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "present"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
import re


def run_cmd(module, host, user, password, cmd):
    conn = Connection(module, host, user, password, command=cmd)
    rc, out = conn.run()
    if rc != 0:
        module.fail_json(msg=f"Command failed: {cmd}", stderr=out)

    if isinstance(out, list):
        cleaned = []
        for line in out:
            cleaned.append(line.encode(
                "utf-8", errors="replace").decode("utf-8"))
        return cleaned
    else:
        return out.encode("utf-8", errors="replace").decode("utf-8")


def normalize(output):
    if isinstance(output, list):
        return "\n".join(output), output
    return output, output.splitlines()


def result_ok(stdout_lines, changed=False):
    stdout = "\n".join(stdout_lines)
    return {"changed": changed, "stdout": stdout, "stdout_lines": stdout_lines}


def show_properties(module, host, user, password):
    stdout, lines = normalize(
        run_cmd(module, host, user, password, "chpvc timezone status"))
    return result_ok(lines)


def show_settings(module, host, user, password):
    stdout, lines = normalize(
        run_cmd(module, host, user, password, "chpvc timezone show"))
    return result_ok(lines)


def get_current_time(module, host, user, password):
    stdout, _ = normalize(
        run_cmd(module, host, user, password, "chpvc timezone status"))
    m = re.search(r"Local time:\s*(.*)", stdout)
    return m.group(1).strip() if m else None


def set_time(module, host, user, password, time_value):
    current = get_current_time(module, host, user, password)
    if current == time_value:
        return result_ok([f"System time already set to {time_value}"], changed=False)

    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", time_value):
        return result_ok(["Invalid time format. Use YYYY-MM-DD HH:MM:SS"], changed=False)

    run_cmd(module, host, user, password,
            f'chpvc timezone set-time "{time_value}"')
    return result_ok([f"System time updated to {time_value}"], changed=True)


def handle_time(module):
    host = module.params["login_host"]
    user = module.params["login_user"]
    password = module.params["login_password"]
    state = module.params["state"]
    action = module.params.get("action")
    value = module.params.get("value")

    if state == "show" and action == "properties":
        return show_properties(module, host, user, password)
    if state == "show" and action == "settings":
        return show_settings(module, host, user, password)
    if state == "present":
        if value:
            return set_time(module, host, user, password, value)
        else:
            current = get_current_time(module, host, user, password)
            return result_ok([current if current else "No system time found"])
    module.fail_json(msg="Invalid state")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=["show", "present"]),
            action=dict(type="str", choices=["settings", "properties"]),
            value=dict(type="str")
        ),
        supports_check_mode=False
    )

    result = handle_time(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
