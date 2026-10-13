#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}

DOCUMENTATION = """
---
module: update
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Update PowerVC cluster using powervc-opsmgr update
description:
  - This module performs update operations on the PowerVC cluster.
  - Supports rolling upgrades, ISO preparation (local path or URL), ISO download,
    and ISO cleanup.
  - Can operate in offline mode and skip remote node upgrades.
notes:
  - Long-running operations (prepare, update) may timeout after 300 seconds.
  - If timeout occurs, the operation continues on the server but Ansible reports failure.
  - For long operations, consider running the command directly on the controller or
    increasing timeout in connection.py.
  - The prepare operation can take 10-30 minutes depending on ISO size.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller.
    required: true
    type: str
  login_user:
    description:
      - SSH User (pvcroot).
    required: true
    type: str
  login_password:
    description:
      - Password for the ssh user.
    required: true
    type: str
  cluster:
    description:
      - Cluster name to deploy updates to.
    required: true
    type: str
  state:
    description:
      - C(present) performs the update/prepare operation.
      - C(absent) performs cleanup (C(--cleanup)).
    required: false
    type: str
    choices: ['present', 'absent']
    default: 'present'
  skip_restart:
    description:
      - Skip restart for tasks which have the restart tag.
    required: false
    type: bool
    default: false
  node:
    description:
      - Hostname or IP of a specific controller node to be updated.
      - Required for standard rolling upgrade unless C(offline_mode) or C(prepare_isopath) is used.
    required: false
    type: str
  force:
    description:
      - Force update operation.
    required: false
    type: bool
    default: false
  verbose:
    description:
      - Enable verbose output during precheck or update.
    required: false
    type: bool
    default: false
  prepare_isopath:
    description:
      - Local ISO path or URL to prepare the system (runs setup-iso and
        opsmgr-only update).
    required: false
    type: str
  http_username:
    description:
      - Username for HTTP Basic Authentication when C(prepare_isopath) is a URL.
    required: false
    type: str
  http_password:
    description:
      - Password for HTTP Basic Authentication when C(prepare_isopath) is a URL.
    required: false
    type: str
    no_log: true
  download_only:
    description:
      - Use with C(prepare_isopath) to only download the ISO without running
        setup-iso or the opsmgr update.
    required: false
    type: bool
    default: false
  download_destination:
    description:
      - Destination directory for ISO download. Defaults to the current directory
        on the controller. Use with C(prepare_isopath) and C(download_only).
    required: false
    type: str
  offline_mode:
    description:
      - Block API and UI calls during update.
      - Most API calls are enabled during a standard rolling update; this option
        blocks all of them.
    required: false
    type: bool
    default: false
  skip_remote_node_upgrade:
    description:
      - Skip remote node upgrade (Novalink, compute plane, cinder backup) during
        PVC rolling or offline upgrade. Remote nodes can be upgraded from the UI
        after the PVC upgrade completes.
    required: false
    type: bool
    default: false
  confirm:
    description:
      - Automatically confirm interactive prompts during cleanup or prepare.
    required: false
    type: str
    choices: ['yes', 'no']
    default: 'yes'
"""

EXAMPLES = """
---
# Example 1: Basic cluster rolling upgrade (specific controller node)
- name: "Update PowerVC cluster"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Perform rolling upgrade on node"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node: "{{ update_node }}"
        state: present
      register: result
    - debug:
        var: result

# Example 2: Prepare system with local ISO path
- name: "Prepare system for update (local ISO)"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run ISO preparation"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        prepare_isopath: "{{ update_prepare_isopath }}"
        verbose: true
      register: result
    - debug:
        var: result

# Example 3: Prepare system by downloading ISO from URL
- name: "Prepare system for update (URL)"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Download and prepare ISO from URL"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        prepare_isopath: "{{ update_prepare_url }}"
        http_username: "{{ update_http_username }}"
        http_password: "{{ update_http_password }}"
      register: result
    - debug:
        var: result

# Example 4: Download ISO only (no setup-iso or update)
- name: "Download ISO only"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Download ISO to destination directory"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        prepare_isopath: "{{ update_prepare_url }}"
        download_only: true
        download_destination: "{{ update_download_destination }}"
        http_username: "{{ update_http_username }}"
        http_password: "{{ update_http_password }}"
      register: result
    - debug:
        var: result

# Example 5: Cleanup ISO
- name: "Cleanup ISO files"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Perform ISO cleanup"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        confirm: "yes"
        state: absent
      register: result
    - debug:
        var: result

# Example 6: Offline mode update
- name: "Update in offline mode"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Perform offline update (all API/UI calls blocked)"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        offline_mode: true
        verbose: true
      register: result
    - debug:
        var: result

# Example 7: Rolling upgrade skipping remote node upgrade
- name: "Update cluster, skip remote node upgrade"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rolling upgrade without upgrading remote nodes"
      ibm.powervc.cli.update:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node: "{{ update_node }}"
        skip_remote_node_upgrade: true
      register: result
    - debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(params):
    """
    Build powervc-opsmgr update command and interactive prompt responses.
    """
    messages = {}

    cluster = params["cluster"]
    state = params["state"]

    command = f"powervc-opsmgr update -c {cluster}"

    # ---------------- CLEANUP ----------------
    if state == "absent":
        command += " --cleanup"
        if params.get("confirm", "yes") == "yes":
            messages[r".*cleanup mounted ISOs.*\(y/n\):"] = "y"
        return command, messages

    # ---------------- PREPARE ISO ----------------
    if params.get("prepare_isopath"):
        command += f" --prepare {params['prepare_isopath']}"
        if params.get("http_username"):
            command += f" --username {params['http_username']}"
        if params.get("http_password"):
            command += f" --password {params['http_password']}"
        if params.get("download_only"):
            command += " --download-only"
        if params.get("download_destination"):
            command += f" --destination {params['download_destination']}"
        if not params.get("download_only") and params.get("confirm", "yes") == "yes":
            messages[r".*cleanup mounted ISOs.*\(y/n\):"] = "y"
        return command, messages

    # ---------------- CONTROLLER UPDATE ----------------
    if params.get("skip_restart"):
        command += " --skip-restart"
    if params.get("node"):
        command += f" -n {params['node']}"
    if params.get("force"):
        command += " -f"
    if params.get("verbose"):
        command += " -v"
    if params.get("offline_mode"):
        command += " -o"
    if params.get("skip_remote_node_upgrade"):
        command += " -sr"

    return command, messages


def run_cli_command():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            cluster=dict(type="str", required=True),
            state=dict(type="str", choices=["present", "absent"], default="present"),
            skip_restart=dict(type="bool", default=False),
            node=dict(type="str"),
            force=dict(type="bool", default=False),
            verbose=dict(type="bool", default=False),
            prepare_isopath=dict(type="str"),
            http_username=dict(type="str"),
            http_password=dict(type="str", no_log=True),
            download_only=dict(type="bool", default=False),
            download_destination=dict(type="str"),
            offline_mode=dict(type="bool", default=False),
            skip_remote_node_upgrade=dict(type="bool", default=False),
            confirm=dict(type="str", choices=["yes", "no"], default="yes"),
        ),
    )

    try:
        p = module.params

        # ---------------- VALIDATION ----------------

        # download_only and download_destination require prepare_isopath
        if p.get("download_only") and not p.get("prepare_isopath"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="download_only requires prepare_isopath to be set.",
            )
        if p.get("download_destination") and not p.get("prepare_isopath"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="download_destination requires prepare_isopath to be set.",
            )

        # http_username / http_password are only meaningful with prepare_isopath
        if (p.get("http_username") or p.get("http_password")) and not p.get("prepare_isopath"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="http_username and http_password are only valid with prepare_isopath.",
            )

        # For a plain rolling upgrade (state=present, no special modes), node is required
        is_plain_update = (
            p["state"] == "present"
            and not p.get("offline_mode")
            and not p.get("prepare_isopath")
        )
        if is_plain_update and not p.get("node"):
            module.fail_json(
                changed=False,
                failed=True,
                msg=(
                    "-n/--node is required for rolling upgrade unless offline_mode "
                    "or prepare_isopath is used."
                ),
            )

        command, messages = construct_command(p)

        connection = Connection(
            module,
            p["login_host"],
            p["login_user"],
            p["login_password"],
            command=command,
            messages=messages,
        )

        rc, output = connection.run()

        # ---------------- NORMALIZE OUTPUT ----------------
        if isinstance(output, str):
            output = output.strip()

        output_list = output if isinstance(output, list) else [str(output)]

        # ---------------- TIMEOUT DETECTION ----------------
        timeout_detected = any(
            "timed out" in str(line).lower() for line in output_list
        )

        success_indicators = any(
            x in " ".join(output_list).lower()
            for x in [
                "cleanup completed successfully",
                "sync and mount successful",
                "updating / installing",
                "completed successfully",
                "found 0 wheels",
            ]
        )

        if timeout_detected and not success_indicators:
            module.exit_json(
                changed=False,
                failed=False,
                warning=True,
                rc=int(rc),
                stdout_lines=output_list,
                msg="Operation timed out. Task may still be running on PowerVC.",
                error="",
            )

        rc = int(rc)
        output = output_list

        # ---------------- POWERVC STATE DETECTION ----------------
        is_blocking_failure = False
        is_healthcheck_issue = False

        for line in output:
            line_lower = str(line).lower()

            if "there seems an earlier operations failure" in line_lower:
                is_blocking_failure = True

            if "health check" in line_lower or "starting health" in line_lower:
                is_healthcheck_issue = True

        # ---------------- DECISION ENGINE ----------------
        changed = False
        failed = False
        warning_flag = False

        if is_blocking_failure:
            failed = True
        elif is_healthcheck_issue and rc == 1:
            warning_flag = True
        elif rc != 0:
            failed = True
        else:
            if p["state"] == "present":
                changed = True
            else:
                changed = False

        # ---------------- RESULT ----------------
        result = dict(
            changed=changed,
            failed=failed,
            warning=warning_flag,
            stdout_lines=output,
            error="",
            rc=rc,
            msg="",
        )

        if warning_flag:
            result["msg"] = "Operation completed with warnings (healthcheck)."

        elif failed:
            error_lines = []
            for line in output:
                clean = str(line).strip()
                if "there seems an earlier operations failure" in clean.lower():
                    error_lines.insert(0, clean)
                elif "ERROR" in clean or "Error" in clean:
                    error_lines.append(clean)
            result["msg"] = (
                error_lines[0]
                if error_lines
                else "PowerVC update failed due to blocking condition."
            )
            result["error"] = result["msg"]

        else:
            if p["state"] == "absent":
                result["msg"] = "ISO cleanup completed successfully"
            elif p.get("prepare_isopath") and p.get("download_only"):
                result["msg"] = "ISO download completed successfully"
            elif p.get("prepare_isopath"):
                result["msg"] = "ISO preparation completed successfully"
            else:
                result["msg"] = "Update operation completed successfully"

        module.exit_json(**result)

    except (CLIError, Exception) as e:
        module.fail_json(changed=False, failed=True, msg=str(e))


def main():
    run_cli_command()


if __name__ == "__main__":
    main()
