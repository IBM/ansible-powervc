#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: scale_config
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC scale configuration settings
description:
  - Manages scale tuning parameters for PowerVC management and compute nodes.
  - Settings are defined in /powervcdata/etc/oslo/scale_params.conf and are
    organised into tiers (small / medium / large).
  - Supports listing current settings, applying scale configurations,
    reverting to defaults, and validating the configuration file.
notes:
  - This module requires SSH access to the PowerVC controller.
  - Scale configuration changes may require service restarts to take effect.
  - Use C(state=show) to view current settings without making changes.
  - Use C(state=validate) to check scale_params.conf syntax without applying.
  - C(quiet) defaults to C(true) so Ansible runs non-interactively; set
    C(quiet=false) only when running manually and a confirmation prompt is desired.
  - All flags are top-level siblings on the CLI; none is a sub-option of another.
    C(--env-type), C(--dry-run), C(--verbose), C(--force), C(--no-restart), and
    C(--restart-timeout) are optional modifiers that accompany C(--apply) but are
    accepted by the parser independently.
options:
  login_host:
    description:
      - IP address or hostname of the PowerVC controller.
    required: true
    type: str
  login_user:
    description:
      - SSH username (typically C(pvcroot)).
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user.
    required: true
    type: str
    no_log: true
  state:
    description:
      - Desired action to perform.
      - C(show) - List current live values vs configured values (read-only).
      - C(present) - Apply scale settings for the tier given by C(env_type).
      - C(absent) - Restore all parameters to their default out-of-box values.
      - C(validate) - Validate scale_params.conf syntax without applying.
    required: true
    type: str
    choices: ['show', 'present', 'absent', 'validate']
  env_type:
    description:
      - Scale tier to use with C(state=present).
      - When omitted, the CLI applies its built-in default (large).
      - C(default) explicitly passes no C(--env-type) flag, letting the CLI decide.
    required: false
    type: str
    choices: ['default', 'small', 'medium', 'large']
  node_type:
    description:
      - Restrict C(state=show) output to one node role (default: all).
    required: false
    type: str
    choices: ['all', 'controller', 'novalink', 'hmc_compute', 'image_node']
  section:
    description:
      - Restrict C(state=show) output to a specific section name.
      - Use C(section=help) to list all available section names.
    required: false
    type: str
  dry_run:
    description:
      - With C(state=present): run the full fetch + diff cycle and print the
        preview table, but do NOT write any changes and do NOT prompt for
        confirmation. Exits after step 4.
    required: false
    type: bool
    default: false
  verbose:
    description:
      - Print each configuration change as it is applied.
    required: false
    type: bool
    default: false
  quiet:
    description:
      - Suppress confirmation prompts (for automation / cron).
      - Defaults to C(true) so Ansible runs non-interactively.
    required: false
    type: bool
    default: true
  force:
    description:
      - Bypass idempotency check; re-apply even if env_type already matches
        the running configuration.
    required: false
    type: bool
    default: false
  no_restart:
    description:
      - Write config files but skip all service restarts. The restart plan is
        still shown. Services continue running on old settings until restarted
        manually or by re-running without this flag.
    required: false
    type: bool
    default: false
  restart_timeout:
    description:
      - Maximum seconds to wait for each Pacemaker resource to come up after a
        restart (default: 120). Per-resource defaults (galera 90s, rabbitmq
        150s, others 60s) are used unless this flag lowers the ceiling.
    required: false
    type: int
'''

EXAMPLES = '''
- name: List current scale configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: List all scale settings
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: show
      register: result

    - name: Display scale settings
      debug:
        var: result.stdout_lines


- name: List scale settings filtered by node type and section
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Show controller settings for a specific section
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: show
        node_type: controller
        section: nova
      register: result

    - name: Display filtered settings
      debug:
        var: result.stdout_lines


- name: Validate scale_params.conf
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Validate config syntax
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: validate
      register: result

    - name: Display validation result
      debug:
        var: result.stdout_lines


- name: Dry-run apply for large tier
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Preview large-tier changes without writing anything
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        env_type: large
        dry_run: true
      register: result

    - name: Display preview
      debug:
        var: result.stdout_lines


- name: Apply scale settings for medium tier
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Apply medium-tier settings quietly
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        env_type: medium
      register: result

    - name: Display apply result
      debug:
        var: result.stdout_lines


- name: Apply scale settings with verbose output and no restart
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Apply large-tier settings, skip restarts
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        env_type: large
        verbose: true
        no_restart: true
        restart_timeout: 180
      register: result

    - name: Display apply result
      debug:
        var: result.stdout_lines


- name: Force re-apply with custom restart timeout
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Re-apply even if env_type already matches
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        env_type: large
        force: true
        restart_timeout: 200
      register: result

    - name: Display result
      debug:
        var: result.stdout_lines


- name: Revert scale settings to defaults
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Restore out-of-box values on all nodes
      ibm.powervc.cli.scale_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: absent
      register: result

    - name: Display revert result
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether the scale configuration was modified.
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string.
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


def handle_show(module, login_host, login_user, login_password,
                node_type, section):

    cmd = "powervc-scale-config --list"

    if node_type and node_type != "all":
        cmd += f" --node-type {node_type}"

    if section:
        cmd += f" --section {section}"

    if module.check_mode:
        return result_ok([f"[CHECK MODE] Would run: {cmd}"], changed=False)

    lines = run_cmd(module, login_host, login_user, login_password, cmd)

    cleaned = clean_output(lines)

    return result_ok(
        cleaned if cleaned else ["No scale settings found"],
        changed=False
    )


def handle_validate(module, login_host, login_user, login_password):

    cmd = "powervc-scale-config --validate"

    if module.check_mode:
        return result_ok([f"[CHECK MODE] Would run: {cmd}"], changed=False)

    lines = run_cmd(module, login_host, login_user, login_password, cmd)

    cleaned = clean_output(lines)

    return result_ok(
        cleaned if cleaned else ["scale_params.conf is valid"],
        changed=False
    )


def handle_present(module, login_host, login_user, login_password,
                   env_type, dry_run, verbose, quiet, force,
                   no_restart, restart_timeout):

    cmd = "powervc-scale-config --apply"

    if env_type and env_type != "default":
        cmd += f" --env-type {env_type}"

    if dry_run:
        cmd += " --dry-run"

    if verbose:
        cmd += " --verbose"

    if quiet:
        cmd += " -q"

    if force:
        cmd += " --force"

    if no_restart:
        cmd += " --no-restart"

    if restart_timeout is not None:
        cmd += f" --restart-timeout {restart_timeout}"

    if module.check_mode:
        return result_ok(
            [f"[CHECK MODE] Would run: {cmd}"],
            changed=not dry_run
        )

    lines = run_cmd(module, login_host, login_user, login_password, cmd)

    cleaned = clean_output(lines)

    # dry-run reads state but writes nothing
    changed = not dry_run

    return result_ok(
        cleaned if cleaned else ["Scale configuration applied successfully"],
        changed=changed
    )


def handle_absent(module, login_host, login_user, login_password, quiet):

    cmd = "powervc-scale-config --revert"

    if quiet:
        cmd += " -q"

    if module.check_mode:
        return result_ok(
            [f"[CHECK MODE] Would run: {cmd}"],
            changed=True
        )

    lines = run_cmd(module, login_host, login_user, login_password, cmd)

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
                choices=["present", "absent", "show", "validate"]
            ),

            # --apply flags
            env_type=dict(
                type="str",
                choices=["default", "small", "medium", "large"]
            ),
            dry_run=dict(type="bool", default=False),
            verbose=dict(type="bool", default=False),
            quiet=dict(type="bool", default=True),
            force=dict(type="bool", default=False),
            no_restart=dict(type="bool", default=False),
            restart_timeout=dict(type="int"),

            # --list flags
            node_type=dict(
                type="str",
                choices=["all", "controller", "novalink", "hmc_compute", "image_node"]
            ),
            section=dict(type="str"),
        ),
        supports_check_mode=True
    )

    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]

    state = module.params["state"]

    if state == "present":

        result = handle_present(
            module,
            login_host,
            login_user,
            login_password,
            env_type=module.params.get("env_type"),
            dry_run=module.params["dry_run"],
            verbose=module.params["verbose"],
            quiet=module.params["quiet"],
            force=module.params["force"],
            no_restart=module.params["no_restart"],
            restart_timeout=module.params.get("restart_timeout"),
        )

    elif state == "absent":

        result = handle_absent(
            module,
            login_host,
            login_user,
            login_password,
            quiet=module.params["quiet"],
        )

    elif state == "show":

        result = handle_show(
            module,
            login_host,
            login_user,
            login_password,
            node_type=module.params.get("node_type"),
            section=module.params.get("section"),
        )

    elif state == "validate":

        result = handle_validate(
            module,
            login_host,
            login_user,
            login_password,
        )

    else:
        module.fail_json(msg="Invalid state")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
