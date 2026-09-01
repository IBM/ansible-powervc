#!/usr/bin/python
from typing import Literal


ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: powervc_log
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage log settings for PowerVC management plane
description:
  - This module manages log settings for various PowerVC services
  - Supports debug configuration for all services or specific service components
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
  service:
    description:
      - PowerVC service to manage log settings for
    required: true
    type: str
    choices: ['general', 'web', 'validation', 'storage', 'self-service',
              'resource-reservation', 'placement', 'network', 'metric',
              'metering', 'image', 'identity', 'event', 'compute']
  action:
    description:
      - Action to perform on the service
    required: true
    type: str
    choices: ['debug']
  state:
    description:
      - State of debug logging (present to enable, absent to disable, show to view)
    required: true
    type: str
    choices: ['present', 'absent', 'show']
  modules:
    description:
      - Comma-separated list of external modules to enable debug logging for
      - Requires restart for changes to take effect
    type: str
  restart:
    description:
      - Restart the service after making changes
      - Required for module changes to take effect
    type: bool
    default: false
  user_response:
    description:
      - Response to interactive confirmation prompts (e.g. "Do you want to proceed? [y/n]")
      - Required when service is 'general' and state is 'present' (enable), as the CLI
        prompts for confirmation before enabling Keystone debug logging
      - Accepted values are 'y' or 'n'
    type: str
    choices: ['y', 'n']
    default: 'y'
"""

EXAMPLES = """
---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "View current debug settings"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "show"
      register: result

    - name: "Display debug settings"
      debug:
        var: result.stdout_lines

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Enable debug (without restart, without modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "present"
        restart: false
      register: result

    - name: "Display result"
      debug:
        var: result.stdout_lines

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Enable debug (with restart, without modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "present"
        restart: true
      register: result

    - name: "Display result"
      debug:
        var: result.stdout_lines

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Enable debug (without restart, with modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "present"
        modules: "{{ modules }}"
        restart: false
      register: result
      when: modules is defined and modules != ""

    - name: "Display result"
      debug:
        var: result.stdout_lines
      when: modules is defined and modules != ""

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Enable debug (with restart, with modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "present"
        modules: "{{ modules }}"
        restart: true
      register: result
      when: modules is defined and modules != ""

    - name: "Display result"
      debug:
        var: result.stdout_lines
      when: modules is defined and modules != ""

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Disable debug (without restart, without modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "absent"
        restart: false
      register: result

    - name: "Display result"
      debug:
        var: result.stdout_lines

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Disable debug (with restart, without modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "absent"
        restart: true
      register: result

    - name: "Display result"
      debug:
        var: result.stdout_lines

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Disable debug (without restart, with modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "absent"
        modules: "{{ modules }}"
        restart: false
      register: result
      when: modules is defined and modules != ""

    - name: "Display result"
      debug:
        var: result.stdout_lines
      when: modules is defined and modules != ""

---
- name: PowerVC Log Management
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Disable debug (with restart, with modules)"
      ibm.powervc.cli.powervc_log:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        service: "{{ service }}"
        action: "debug"
        state: "absent"
        modules: "{{ modules }}"
        restart: true
      register: result
      when: modules is defined and modules != ""

    - name: "Display result"
      debug:
        var: result.stdout_lines
      when: modules is defined and modules != ""
"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd, messages=None):
    """Run command via SSH connection"""
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd, messages=messages or {})
    rc, out = conn.run()

    if rc != 0:
        stderr_msg = "\n".join(out) if isinstance(out, list) else str(out)
        module.fail_json(msg=f"Command failed: {cmd}", stderr=stderr_msg)

    if isinstance(out, list):
        return "\n".join(out), out

    return out, out


def result_ok(lines, changed=False):
    """Format result output"""
    return {
        "changed": changed,
        "stdout": "\n".join(lines) if isinstance(lines, list) else lines,
        "stdout_lines": lines if isinstance(lines, list) else [lines]
    }


def handle_debug(module, login_host, login_user, login_password, service, state, modules, restart, user_response):
    """Handle debug configuration for PowerVC services"""

    # Build base command
    cmd = f"powervc-log {service} debug"

    # If state is show, just run the command without options
    if state == "show":
        _, lines = run_cmd(module, login_host, login_user, login_password, cmd)
        return result_ok(lines if lines else [f"Current debug settings for {service}"], changed=False)

    # Add enable/disable flag based on state
    if state == "present":
        cmd += " --enable"
    elif state == "absent":
        cmd += " --disable"

    # Add modules if specified
    if modules:
        cmd += f" -m {modules}"

    # Add restart flag if specified
    if restart:
        cmd += " --restart"

    # Only 'general' + --enable prompts "Do you want to proceed? [y/n]"
    # before touching Keystone.  --disable on general and all other
    # services run non-interactively — no prompt, no PTY needed.
    messages = {}
    if service == "general" and state == "present":
        messages = {r"Do you want to proceed\? \[y/n\]": user_response}

    # Execute command
    _, lines = run_cmd(module, login_host, login_user, login_password, cmd, messages=messages)

    changed = state in ["present", "absent"]
    action_msg: Literal['enabled', 'disabled',
                        'configured'] = "enabled" if state == "present" else "disabled" if state == "absent" else "configured"
    return result_ok(
        lines if lines else [f"Debug {action_msg} for {service} service"],
        changed=changed
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            service=dict(
                type="str",
                required=True,
                choices=[
                    'general', 'web', 'validation', 'storage', 'self-service',
                    'resource-reservation', 'placement', 'network', 'metric',
                    'metering', 'image', 'identity', 'event', 'compute'
                ]
            ),
            action=dict(type="str", required=True, choices=["debug"]),
            state=dict(type="str", required=True, choices=[
                       "present", "absent", "show"]),
            modules=dict(type="str"),
            restart=dict(type="bool", default=False),
            user_response=dict(type="str", default="y", choices=["y", "n"]),
        ),
        supports_check_mode=False
    )

    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    service = module.params["service"]
    action = module.params["action"]
    state = module.params["state"]
    modules = module.params.get("modules")
    restart = module.params["restart"]
    user_response = module.params["user_response"]

    if action == "debug":
        result = handle_debug(
            module, login_host, login_user, login_password,
            service, state, modules, restart, user_response
        )
    else:
        module.fail_json(msg="Invalid action")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
