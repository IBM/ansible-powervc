#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
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
      - State of time operations. Use C(show) to display time information,
        C(present) to set the system time when C(value) is provided, or to
        display the current time when C(value) is omitted.
    required: true
    type: str
    choices: ['show', 'present']
  action:
    description:
      - Sub-action for C(state=show). Use C(settings) to display time show
        output, C(properties) to display time status output.
    required: false
    type: str
    choices: ['settings', 'properties']
  value:
    description:
      - Time value to set. When C(state=present) and C(value) is provided,
        the system time is updated. When C(value) is omitted with
        C(state=present), the current system time is displayed (read-only).
        Format must be C(YYYY-MM-DD HH:MM:SS).
    required: false
    type: str
'''

EXAMPLES = '''
- name: "Show time settings"
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
        action: "settings"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Show time properties"
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
        action: "properties"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Set system time"
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
        value: "2025-06-01 10:00:00"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Show current system time"
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
'''

RETURN = '''
stdout:
  description: Raw command output as a single string.
  returned: always
  type: str
stdout_lines:
  description: Command output split into a list of lines.
  returned: always
  type: list
  elements: str
changed:
  description: Whether a system change was made.
  returned: always
  type: bool
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
import re


def run_cmd(module, host, user, password, cmd):
    conn = Connection(module, host, user, password, command=cmd)
    rc, out = conn.run()
    if rc != 0:
        module.fail_json(msg=f"Command failed: {cmd}", stdout=out, rc=rc)

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
    _, lines = normalize(
        run_cmd(module, host, user, password, "chpvc time status"))
    return result_ok(lines)


def show_settings(module, host, user, password):
    _, lines = normalize(
        run_cmd(module, host, user, password, "chpvc time show"))
    return result_ok(lines)


def get_current_time(module, host, user, password):
    stdout, _ = normalize(
        run_cmd(module, host, user, password, "chpvc time status"))
    m = re.search(r"Local time:\s*(.*)", stdout)
    return m.group(1).strip() if m else None


def set_time(module, host, user, password, time_value):
    # validate format and fail hard so playbook error handling triggers
    if not re.match(r"^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$", time_value):
        module.fail_json(
            msg=f"Invalid time format '{time_value}'. Expected YYYY-MM-DD HH:MM:SS"
        )

    # idempotency — compare at minute granularity (HH:MM) because the live
    # clock string ("Sun 2025-06-01 10:00:02 UTC") shifts by seconds each run.
    # Comparing "YYYY-MM-DD HH:MM" is stable and catches same-day time changes.
    current_raw = get_current_time(module, host, user, password)
    desired_dt = time_value[:16]   # "YYYY-MM-DD HH:MM"
    live_dt = None
    if current_raw:
        dtm = re.search(r"(\d{4}-\d{2}-\d{2} \d{2}:\d{2})", current_raw)
        live_dt = dtm.group(1) if dtm else None

    if live_dt == desired_dt:
        return result_ok(
            [f"System time already at {desired_dt}"],
            changed=False
        )

    # honour check mode — report what would change without acting
    if module.check_mode:
        return result_ok(
            [f"[CHECK MODE] Would set system time to {time_value}"],
            changed=True
        )

    run_cmd(module, host, user, password,
            f'chpvc time set-time "{time_value}"')
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
        # Read-only path: runs even in check_mode (no state change)
        current = get_current_time(module, host, user, password)
        return result_ok([current if current else "No system time found"])
    module.fail_json(
        msg=f"Invalid state/action combination: state='{state}', action='{action}'"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=["show", "present"]),
            action=dict(type="str", required=False, choices=["settings", "properties"]),
            value=dict(type="str", required=False)
        ),
        # enforce that action is supplied when state=show
        required_if=[
            ("state", "show", ["action"]),
        ],
        supports_check_mode=True
    )

    result = handle_time(module)
    module.exit_json(**result)


if __name__ == "__main__":
    main()
