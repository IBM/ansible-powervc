#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: scale_config
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC scale configuration settings
description:
  - Manages scale tuning parameters for PowerVC management and novalink nodes
  - These settings are intended for high scale environments and have memory impact
  - Uses settings defined in /powervcdata/etc/oslo/scale.conf
  - Supports listing current settings, applying scale configurations, and reverting changes
  - Can set service-specific configurations for supported PowerVC services
notes:
  - This module requires SSH access to the PowerVC controller
  - Scale configuration changes may require service restarts to take effect
  - Settings are applied from /powervcdata/etc/oslo/scale.conf
  - Use 'state: show' to view current settings without making changes
options:
  login_host:
    description:
      - IP address or hostname of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH username (typically 'pvcroot')
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user
    required: true
    type: str
    no_log: true
  state:
    description:
      - Desired state of the scale configuration
      - C(show) - List current scale settings (read-only, no changes made)
      - C(present) - Apply scale settings from scale.conf or set service configuration
      - C(absent) - Revert configuration to state before scale settings were applied
    required: false
    type: str
    choices: ['show', 'present', 'absent']
    default: 'show'
  set_config:
    description:
      - List of service configuration settings to apply
      - Each item should be in format 'service.parameter=value'
      - Currently supported service is 'nova-compute-svc'
      - Common parameters include 'workers' and 'threads'
      - When provided with C(state: present), sets specific service configurations
      - When omitted with C(state: present), applies all settings from scale.conf
    required: false
    type: list
    elements: str
    examples:
      - "nova-compute-svc.workers=10"
      - "nova-compute-svc.threads=5"
"""

EXAMPLES = """
---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: List current scale configuration
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: show
      register: result

    - name: "Display result"
      debug:
        var: result.stdout_lines


---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: Apply scale settings from scale.conf
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
      register: result

    - name: "Show result"
      debug:
        var: result.stdout_lines


---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: Configure nova-compute-svc
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        service: "{{ scale_config_service}}"
        memory_max: "{{ scale_config_memory_max }}"
      register: result

    - debug:
        var: result.stdout_lines


---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: Configure nova-compute-svc on specific host
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        service: "{{ scale_config_service }}"
        memory_max: "{{ scale_config_memory_max }}"
        host: "{{ scale_config_host }}"
      register: result

    - debug:
        var: result.stdout_lines


---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: Configure nova-compute-svc and restart service
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        service: "{{ scale_config_service }}"
        memory_max: "{{ scale_config_memory_max }}"
        restart: true
      register: result

    - debug:
        var: result.stdout_lines


---
- name: Manage PowerVC Scale Configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Information Only"
      debug:
        msg:
          - "This operation may take several minutes."
          - "Please wait while tasks are running."

    - name: Revert scale settings
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: absent
      register: result

    - debug:
        var: result.stdout_lines

"""

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd):
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd)

    rc, out = conn.run()

    if rc != 0:
        stderr_msg = "\n".join(out) if isinstance(out, list) else str(out)
        module.fail_json(
            msg=f"Command failed: {cmd}",
            stderr=stderr_msg
        )

    if isinstance(out, list):
        return out

    return [str(out)]


def result_ok(lines, changed=False):
    return {
        "changed": changed,
        "stdout": "\n".join(lines),
        "stdout_lines": lines
    }


def clean_output(lines):
    cleaned = []

    for line in lines:
        line = line.strip()

        if not line:
            continue

        if line.startswith("+"):
            continue

        cleaned.append(line)

    return cleaned


def handle_show(module, login_host, login_user, login_password):

    cmd = "powervc-scale-config --list"

    lines = run_cmd(module, login_host, login_user, login_password, cmd)

    cleaned = clean_output(lines)

    return result_ok(
        cleaned if cleaned else ["No scale settings found"],
        changed=False
    )


def handle_present(module, login_host, login_user, login_password, service, memory_max, restart, host):

    # Apply settings from scale.conf
    if not service:
        cmd = "powervc-scale-config --apply"

    # Update service configuration
    else:
        cmd = f"powervc-scale-config --set {service}"

        has_parameter = False

        if memory_max:
            cmd += f" MemoryMax={memory_max}"
            has_parameter = True

        if host:
            cmd += f" host={host}"
            has_parameter = True

        if restart is not None:
            cmd += f" restart={'true' if restart else 'false'}"
            has_parameter = True

        if not has_parameter:
            module.fail_json(
                msg=(
                    "When service is specified, at least one of "
                    "memory_max, host, or restart must be provided."
                )
            )

    lines = run_cmd(
        module,
        login_host,
        login_user,
        login_password,
        cmd
    )

    cleaned = clean_output(lines)

    return result_ok(
        cleaned if cleaned else ["Scale configuration applied successfully"],
        changed=True
    )


def handle_absent(module, login_host, login_user, login_password):

    cmd = "powervc-scale-config --revert"

    lines = run_cmd(
        module,
        login_host,
        login_user,
        login_password,
        cmd
    )

    cleaned = clean_output(lines)

    return result_ok(
        cleaned if cleaned else ["Scale configuration reverted successfully"],
        changed=True
    )


def main():

    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),

            state=dict(
                type="str",
                required=True,
                choices=["present", "absent", "show"]
            ),

            service=dict(
                type="str",
                choices=["nova-compute-svc"]
            ),

            memory_max=dict(type="str"),
            host=dict(type="str"),
            restart=dict(type="bool")
        ),
        supports_check_mode=False
    )

    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]

    state = module.params["state"]

    service = module.params.get("service")
    memory_max = module.params.get("memory_max")
    host = module.params.get("host")
    restart = module.params.get("restart")

    if state == "present":

        result = handle_present(
            module,
            login_host,
            login_user,
            login_password,
            service,
            memory_max,
            host,
            restart
        )

    elif state == "absent":

        result = handle_absent(
            module,
            login_host,
            login_user,
            login_password
        )

    elif state == "show":

        result = handle_show(
            module,
            login_host,
            login_user,
            login_password
        )

    else:
        module.fail_json(msg="Invalid state")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
