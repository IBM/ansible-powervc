#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: timezone
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Mnages timezone operations of PowerVC
description:
  - This module displays and sets timezone
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
      - State of timezone operation
    required: true
    type: str
  value:
    description:
      - Timezone value to be set
    type: str
"""

EXAMPLE = """
---
- name: "Manage PowerVC timezone commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Set timezone"
      ibm.powervc.cli.timezone:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "present"
        value: "{{ timezone_value }}"
      register: result

    - name: "Show command output"
      debug:
        var: result.stdout_lines

---
- name: "Manage PowerVC timezone commands"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Show current timezone"
      ibm.powervc.cli.timezone:
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
    return out


def normalize(output):
    """Return stdout, stdout_lines"""
    if isinstance(output, list):
        return "\n".join(output), output
    return output, output.splitlines()


def result_ok(stdout_lines, changed=False, extra=None):
    stdout = "\n".join(stdout_lines)
    res = {"changed": changed, "stdout": stdout, "stdout_lines": stdout_lines}
    if extra:
        res.update(extra)
    return res


def clean_timezone_lines(lines):
    cleaned = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith("+") or "End of chpvc" in line or "INFO" in line or "\x1b" in line:
            continue
        cleaned.append(line)
    return cleaned


def get_current_timezone(module, host, user, password):
    stdout, lines = normalize(
        run_cmd(module, host, user, password, "chpvc timezone status"))
    for line in lines:
        if "Time zone:" in line:
            # Extract timezone value after "Time zone:" - matches both "Region/City" and standalone like "UTC"
            m = re.search(r"Time zone:\s*([A-Za-z_]+(?:/[A-Za-z_]+)?)", line)
            if m:
                return m.group(1).strip()
    return None


def timezone_list(module, host, user, password):
    stdout, lines = normalize(
        run_cmd(module, host, user, password, "chpvc timezone list-timezones"))
    return clean_timezone_lines(lines)


def set_timezone(module, host, user, password, tz):
    current = get_current_timezone(module, host, user, password)
    valid = timezone_list(module, host, user, password)

    if tz not in valid:
        return result_ok(
            [f"Invalid timezone: {tz}. Valid timezones: {', '.join(valid)}"],
            changed=False,
            extra={"valid_timezones": valid}
        )

    if current == tz:
        return result_ok([f"Timezone already set to {tz}"], changed=False)

    run_cmd(module, host, user, password, f"chpvc timezone set-timezone {tz}")
    return result_ok([f"Timezone updated to {tz}"], changed=True)


def handle_timezone(module):
    host = module.params["login_host"]
    user = module.params["login_user"]
    password = module.params["login_password"]
    state = module.params["state"]
    value = module.params.get("value")

    if state == "present":
        if value:
            return set_timezone(module, host, user, password, value)
        else:
            current = get_current_timezone(module, host, user, password)
            return result_ok([current if current else "No timezone found"])

    module.fail_json(msg="Invalid state")


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=[
                       "supported_list", "present"]),
            value=dict(type="str")
        ),
        supports_check_mode=False
    )

    result = handle_timezone(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
