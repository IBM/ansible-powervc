#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}

DOCUMENTATION = """
---
module: ifix
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC iFixes using powervc-opsmgr
description:
  - This module manages intermediate fixes (iFixes) on the PowerVC cluster.
  - Supports listing applied ifixes and applying ifixes on controller nodes
    and remote nodes (novalinks and image nodes).
notes:
  - Long-running operations may exceed standard timeouts.
  - Remote-node ifix options (C(remote_node), C(all_remotenodes), C(all_novalinks),
    C(all_imagenodes), C(apply_specificnodes), C(skip_remotenodes_ifix)) cannot be
    combined with C(node) / C(-n).
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
      - Cluster name to manage iFixes for.
    required: true
    type: str
  list_ifixes:
    description:
      - List applied ifixes from the cluster.
      - For controller-node ifixes omit C(remote_node). For remote-node ifixes
        combine with C(remote_node=true).
    required: false
    type: bool
    default: false
  ifix_isopath:
    description:
      - Absolute path of the ifix ISO file on the controller.
    required: false
    type: str
  remote_node:
    description:
      - Operate on remote nodes (novalinks and image nodes).
      - Must be combined with one of C(all_remotenodes), C(all_novalinks),
        C(all_imagenodes), C(apply_specificnodes), C(skip_remotenodes_ifix),
        or C(list_ifixes).
      - Cannot be combined with C(node).
    required: false
    type: bool
    default: false
  all_remotenodes:
    description:
      - Apply ifix on all remote nodes (novalinks + image nodes).
      - Requires C(remote_node=true) and C(ifix_isopath).
    required: false
    type: bool
    default: false
  all_novalinks:
    description:
      - Apply ifix on all novalink nodes only.
      - Requires C(remote_node=true) and C(ifix_isopath).
    required: false
    type: bool
    default: false
  all_imagenodes:
    description:
      - Apply ifix on all image nodes only.
      - Requires C(remote_node=true) and C(ifix_isopath).
    required: false
    type: bool
    default: false
  apply_specificnodes:
    description:
      - Apply ifix only on the specified remote node IPs/hostnames.
      - Requires C(remote_node=true) and C(ifix_isopath).
    required: false
    type: list
    elements: str
  skip_remotenodes_ifix:
    description:
      - Skip ifix on the specified remote node IPs/hostnames; apply to all others.
      - Requires C(remote_node=true) and C(ifix_isopath).
    required: false
    type: list
    elements: str
  node:
    description:
      - Hostname or IP of a specific controller node to target.
      - Applicable for targeting a specific controller node when applying an ifix
        or listing ifixes.
      - Cannot be combined with C(remote_node).
    required: false
    type: str
  force:
    description:
      - Force ifix operation. Automatically confirms interactive prompts when prompted.
    required: false
    type: bool
    default: false
  verbose:
    description:
      - Enable verbose output during ifix operation.
    required: false
    type: bool
    default: false
"""

EXAMPLES = """
---
# Example 1: List controller-node ifixes
- name: "List controller ifixes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Get list of applied ifixes on controller nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        list_ifixes: true
      register: result
    - debug:
        var: result

# Example 2: List remote-node ifixes
- name: "List remote-node ifixes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List ifixes on remote nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        list_ifixes: true
      register: result
    - debug:
        var: result

# Example 3: List ifixes on a specific controller node
- name: "List ifixes on specific controller node"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List ifixes on specific node"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node: "{{ ifix_node }}"
        list_ifixes: true
      register: result
    - debug:
        var: result

# Example 4: Apply ifix on a specific controller node
- name: "Apply ifix on controller node"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix from ISO on specific controller node"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node: "{{ ifix_node }}"
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 5: Apply ifix to all remote nodes
- name: "Apply ifix to all remote nodes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix on all novalinks and image nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        all_remotenodes: true
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 6: Apply ifix to all novalinks only
- name: "Apply ifix to all novalinks"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix on all novalink nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        all_novalinks: true
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 7: Apply ifix to all image nodes only
- name: "Apply ifix to all image nodes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix on all image nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        all_imagenodes: true
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 8: Apply ifix to specific remote nodes
- name: "Apply ifix to specific remote nodes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix on selected nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        apply_specificnodes: "{{ ifix_apply_specificnodes }}"
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 9: Apply ifix to all remote nodes except some
- name: "Apply ifix skipping certain remote nodes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Apply ifix, skip specified remote nodes"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        remote_node: true
        skip_remotenodes_ifix: "{{ ifix_skip_remotenodes_ifix }}"
        ifix_isopath: "{{ ifix_isopath }}"
      register: result
    - debug:
        var: result

# Example 10: Force apply ifix on controller node
- name: "Force apply ifix on controller node"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Force apply ifix from ISO on controller node"
      ibm.powervc.cli.ifix:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node: "{{ ifix_node }}"
        ifix_isopath: "{{ ifix_isopath }}"
        force: true
        verbose: true
      register: result
    - debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(params):
    """
    Build powervc-opsmgr update command for iFix operations and interactive prompt responses.
    """
    messages = {}
    cluster = params["cluster"]

    command = f"powervc-opsmgr update -c {cluster}"

    # ---------------- LIST IFIXES ----------------
    if params.get("list_ifixes"):
        if params.get("remote_node"):
            command += " -r"
        command += " -l"
        if params.get("node"):
            command += f" -n {params['node']}"
        return command, messages

    # ---------------- REMOTE NODE IFIX ----------------
    if params.get("remote_node"):
        command += " -r"
        if params.get("all_remotenodes"):
            command += " --all-remotenodes"
        if params.get("all_novalinks"):
            command += " --all-novalinks"
        if params.get("all_imagenodes"):
            command += " --all-imagenodes"
        if params.get("apply_specificnodes"):
            nodes_str = " ".join(params["apply_specificnodes"])
            command += f" --apply-specificnodes {nodes_str}"
        if params.get("skip_remotenodes_ifix"):
            nodes_str = " ".join(params["skip_remotenodes_ifix"])
            command += f" --skip-remotenodes-ifix {nodes_str}"
        if params.get("ifix_isopath"):
            command += f" --ifix-isopath {params['ifix_isopath']}"
        if params.get("force"):
            command += " -f"
            messages[
                r".*Do you want to continue force applying iFix.*Please confirm \(yes/no\):"
            ] = "yes"
        if params.get("verbose"):
            command += " -v"
        return command, messages

    # ---------------- CONTROLLER IFIX ----------------
    if params.get("node"):
        command += f" -n {params['node']}"
    if params.get("ifix_isopath"):
        command += f" --ifix-isopath {params['ifix_isopath']}"
    if params.get("force"):
        command += " -f"
        messages[
            r".*Do you want to continue force applying iFix.*Please confirm \(yes/no\):"
        ] = "yes"
    if params.get("verbose"):
        command += " -v"

    return command, messages


def run_cli_command():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            cluster=dict(type="str", required=True),
            list_ifixes=dict(type="bool", default=False),
            ifix_isopath=dict(type="str"),
            remote_node=dict(type="bool", default=False),
            all_remotenodes=dict(type="bool", default=False),
            all_novalinks=dict(type="bool", default=False),
            all_imagenodes=dict(type="bool", default=False),
            apply_specificnodes=dict(type="list", elements="str"),
            skip_remotenodes_ifix=dict(type="list", elements="str"),
            node=dict(type="str"),
            force=dict(type="bool", default=False),
            verbose=dict(type="bool", default=False),
        ),
        mutually_exclusive=[
            ["node", "remote_node"],
        ],
    )

    try:
        p = module.params

        # ---------------- VALIDATION ----------------

        # Require either list_ifixes or ifix_isopath
        if not p.get("list_ifixes") and not p.get("ifix_isopath"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="Either list_ifixes=true or ifix_isopath must be specified.",
            )

        # remote_node requires a targeting flag or list_ifixes
        if p.get("remote_node") and not p.get("list_ifixes"):
            remote_flags = (
                p.get("all_remotenodes")
                or p.get("all_novalinks")
                or p.get("all_imagenodes")
                or p.get("apply_specificnodes")
                or p.get("skip_remotenodes_ifix")
            )
            if not remote_flags:
                module.fail_json(
                    changed=False,
                    failed=True,
                    msg=(
                        "remote_node=true requires one of: all_remotenodes, all_novalinks, "
                        "all_imagenodes, apply_specificnodes, skip_remotenodes_ifix, or list_ifixes."
                    ),
                )

        # remote_node ifix targeting requires ifix_isopath
        remote_ifix_targeting = (
            p.get("all_remotenodes")
            or p.get("all_novalinks")
            or p.get("all_imagenodes")
            or p.get("apply_specificnodes")
            or p.get("skip_remotenodes_ifix")
        )
        if remote_ifix_targeting and not p.get("ifix_isopath"):
            module.fail_json(
                changed=False,
                failed=True,
                msg=(
                    "ifix_isopath is required when using remote node ifix targeting options "
                    "(all_remotenodes, all_novalinks, all_imagenodes, apply_specificnodes, "
                    "skip_remotenodes_ifix)."
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
                "completed successfully",
                "updating / installing",
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
            if p.get("list_ifixes"):
                changed = False
            else:
                changed = True

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
                else "PowerVC ifix operation failed due to blocking condition."
            )
            result["error"] = result["msg"]

        else:
            if p.get("list_ifixes"):
                result["msg"] = "Successfully retrieved ifix list"
            else:
                result["msg"] = "iFix installation completed successfully"

        module.exit_json(**result)

    except (CLIError, Exception) as e:
        module.fail_json(changed=False, failed=True, msg=str(e))


def main():
    run_cli_command()


if __name__ == "__main__":
    main()
