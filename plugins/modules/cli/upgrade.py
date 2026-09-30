#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}

DOCUMENTATION = """
---
module: upgrade
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Upgrade PowerVC cluster using powervc-opsmgr upgrade
description:
  - This module performs upgrade operations on the PowerVC cluster using
    C(powervc-opsmgr upgrade).
  - Supports full cluster rolling upgrades, forced upgrades, pre-upgrade
    and post-upgrade Base OS configuration tasks, and skipping remote node
    upgrades.
  - C(preupgrade) and C(postupgrade) are mutually exclusive — only one may
    be specified per task.
notes:
  - Upgrade operations are long-running and may exceed the default SSH
    connection timeout. If a timeout occurs the operation continues on the
    server; Ansible will report a warning rather than a hard failure.
  - C(preupgrade) runs pre-configuration tasks on the specified node before
    a Base OS upgrade is performed.
  - C(postupgrade) runs post-configuration tasks on the specified node after
    a Base OS upgrade has completed.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller.
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot)).
    required: true
    type: str
  login_password:
    description:
      - Password for the SSH user.
    required: true
    type: str
  cluster:
    description:
      - Cluster name to deploy the upgrade to.
    required: true
    type: str
  force:
    description:
      - Force the upgrade operation.
    required: false
    type: bool
    default: false
  verbose:
    description:
      - Enable verbose output during precheck or upgrade.
    required: false
    type: bool
    default: false
  skip_remote_node_upgrade:
    description:
      - Skip remote node (Novalink, cinder image node) upgrade during the
        PVC rolling upgrade. Remote nodes can be upgraded from the UI after
        the PVC upgrade completes.
    required: false
    type: bool
    default: false
  preupgrade:
    description:
      - IP address of the node on which to run pre-configuration tasks
        before a Base OS upgrade.
      - Mutually exclusive with C(postupgrade).
    required: false
    type: str
  postupgrade:
    description:
      - IP address of the node on which to run post-configuration tasks
        after a Base OS upgrade.
      - Mutually exclusive with C(preupgrade).
    required: false
    type: str
"""

EXAMPLES = """
---
# Example 1: Full cluster rolling upgrade
- name: "PowerVC Upgrade - Full Cluster Upgrade"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Perform full cluster rolling upgrade"
      ibm.powervc.cli.upgrade:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result
    - debug:
        var: result

# Example 2: Force upgrade
- name: "PowerVC Upgrade - Force Upgrade"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Force cluster upgrade with verbose output"
      ibm.powervc.cli.upgrade:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        force: "{{ upgrade_force }}"
        verbose: "{{ upgrade_verbose }}"
      register: result
    - debug:
        var: result

# Example 3: Upgrade skipping remote node upgrade
- name: "PowerVC Upgrade - Skip Remote Node Upgrade"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Upgrade cluster without upgrading Novalink/cinder-image remote nodes"
      ibm.powervc.cli.upgrade:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        skip_remote_node_upgrade: "{{ upgrade_skip_remote_node_upgrade }}"
      register: result
    - debug:
        var: result

# Example 4: Run pre-upgrade tasks on a node before Base OS upgrade
- name: "PowerVC Upgrade - Pre-Upgrade Configuration"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run pre-config tasks on node before Base OS upgrade"
      ibm.powervc.cli.upgrade:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        preupgrade: "{{ upgrade_node_ip }}"
        verbose: "{{ upgrade_verbose }}"
      register: result
    - debug:
        var: result

# Example 5: Run post-upgrade tasks on a node after Base OS upgrade
- name: "PowerVC Upgrade - Post-Upgrade Configuration"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Run post-config tasks on node after Base OS upgrade"
      ibm.powervc.cli.upgrade:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        postupgrade: "{{ upgrade_node_ip }}"
        verbose: "{{ upgrade_verbose }}"
      register: result
    - debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(params):
    """
    Build the powervc-opsmgr upgrade command and interactive prompt responses.
    """
    messages = {}

    command = f"powervc-opsmgr upgrade -c {params['cluster']}"

    if params.get("force"):
        command += " -f"

    if params.get("verbose"):
        command += " -v"

    if params.get("skip_remote_node_upgrade"):
        command += " -sr"

    # preupgrade and postupgrade are mutually exclusive (enforced by AnsibleModule)
    if params.get("preupgrade"):
        command += f" --preupgrade {params['preupgrade']}"
    elif params.get("postupgrade"):
        command += f" --postupgrade {params['postupgrade']}"

    return command, messages


def run_cli_command():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            cluster=dict(type="str", required=True),
            force=dict(type="bool", default=False),
            verbose=dict(type="bool", default=False),
            skip_remote_node_upgrade=dict(type="bool", default=False),
            preupgrade=dict(type="str"),
            postupgrade=dict(type="str"),
        ),
        mutually_exclusive=[
            ["preupgrade", "postupgrade"],
        ],
    )

    try:
        p = module.params

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
                "upgrade completed",
                "post-config completed",
                "pre-config completed",
            ]
        )

        if timeout_detected and not success_indicators:
            module.exit_json(
                changed=False,
                failed=False,
                warning=True,
                rc=int(rc),
                stdout_lines=output_list,
                msg="Operation timed out. Upgrade may still be running on PowerVC.",
                error="",
            )

        rc = int(rc)
        output = output_list

        # ---------------- FAILURE DETECTION ----------------
        is_blocking_failure = any(
            "there seems an earlier operations failure" in str(line).lower()
            for line in output
        )

        failed = is_blocking_failure or rc != 0
        changed = not failed

        # ---------------- RESULT ----------------
        result = dict(
            changed=changed,
            failed=failed,
            warning=False,
            stdout_lines=output,
            error="",
            rc=rc,
            msg="",
        )

        if failed:
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
                else "PowerVC upgrade failed."
            )
            result["error"] = result["msg"]
        else:
            if p.get("preupgrade"):
                result["msg"] = "Pre-upgrade configuration completed successfully"
            elif p.get("postupgrade"):
                result["msg"] = "Post-upgrade configuration completed successfully"
            else:
                result["msg"] = "Upgrade completed successfully"

        module.exit_json(**result)

    except (CLIError, Exception) as e:
        module.fail_json(changed=False, failed=True, msg=str(e))


def main():
    run_cli_command()


if __name__ == "__main__":
    main()
