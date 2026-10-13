#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}

DOCUMENTATION = """
---
module: cert_checks
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage and check PowerVC certificates using powervc-opsmgr
description:
  - This module wraps C(powervc-opsmgr config certs) to validate a CA certificate,
    copy CA cert/key to the standard path, generate service certificates, sync
    certificates to other nodes, restart services, check certificate expiry and
    roll back to the PowerVC provided certificates.
notes:
  - C(validate) is read-only. C(check_expiry) is read-only. All other actions
    report C(changed=true) on success.
  - C(validate) requires C(ca_cert) (enforced by the CLI).
  - C(chain) can only be used together with C(validate).
  - Long-running operations may exceed standard timeouts.
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
      - Cluster name on which the certs sub-command is executed.
    required: true
    type: str
  ca_cert:
    description:
      - Path to the CA certificate file on the controller.
      - Required when C(validate=true).
    required: false
    type: str
  ca_key:
    description:
      - Path to the CA key file on the controller.
    required: false
    type: str
  copy:
    description:
      - Copy the CA cert and key to the standard path (C(--copy)).
    required: false
    type: bool
    default: false
  rollback:
    description:
      - Roll back to the PowerVC provided certificates (C(--rollback)).
    required: false
    type: bool
    default: false
  validate:
    description:
      - Perform CA certificate checks (C(--validate)). Requires C(ca_cert).
    required: false
    type: bool
    default: false
  chain:
    description:
      - Check the certificate chain (C(--chain)). Only valid with C(validate=true).
    required: false
    type: bool
    default: false
  cert_type:
    description:
      - Generate a certificate for the given service type (C(--type)).
    required: false
    type: str
    choices: [rabbit, zookeeper, powervc, novnc, db, memcached]
  sync:
    description:
      - Sync certs to other nodes (C(--sync)).
      - C(default) passes C(--sync) with no argument (secondary controller nodes).
      - C(secondary), C(nl) (novalink) or C(bn) (backup node) pass the value explicitly.
    required: false
    type: str
    choices: [default, secondary, nl, bn]
  restart:
    description:
      - Restart PowerVC services (C(--restart)).
      - C(default) passes C(--restart) with no argument.
      - C(nl) (novalink) or C(bn) (backup node) pass the value explicitly.
    required: false
    type: str
    choices: [default, nl, bn]
  check_expiry:
    description:
      - Check expiry of certs (C(--check-expiry)).
      - C(default) passes C(--check-expiry) with no argument (controller certs).
      - C(nl) (novalink) or C(bn) (backup node) pass the value explicitly.
      - The returned table is parsed into the C(certificates) result list; each entry
        has C(path), C(expiration_date), C(days_remaining) and C(expired).
    required: false
    type: str
    choices: [default, nl, bn]
  verbose:
    description:
      - Enable verbose output.
    required: false
    type: bool
    default: false
"""

EXAMPLES = """
---
# Example 1: Validate a CA certificate including its chain
- name: "Validate CA certificate chain"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Validate CA cert and chain"
      ibm.powervc.cli.cert_checks:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        ca_cert: /root/ca/ca.crt
        validate: true
        chain: true
      register: result

# Example 2: Check certificate expiry on the controller
- name: "Check certificate expiry"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Check expiry"
      ibm.powervc.cli.cert_checks:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        check_expiry: default
      register: result

# Example 3: Copy CA cert/key, generate a service cert and sync to other nodes
- name: "Install custom CA certificates"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Copy CA cert and key"
      ibm.powervc.cli.cert_checks:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        ca_cert: /root/ca/ca.crt
        ca_key: /root/ca/ca.key
        copy: true

    - name: "Generate powervc certificate and sync"
      ibm.powervc.cli.cert_checks:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        cert_type: powervc
        sync: default

# Example 4: Roll back to the PowerVC provided certificates
- name: "Rollback certificates"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Rollback"
      ibm.powervc.cli.cert_checks:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        rollback: true
"""

import re
from datetime import datetime, timezone

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


# Actions that only read state; if none of the mutating actions is requested
# the module reports changed=False.
MUTATING_ACTIONS = ("copy", "rollback", "cert_type", "sync", "restart")
ALL_ACTIONS = MUTATING_ACTIONS + ("validate", "check_expiry")


_TABLE_ROW = re.compile(r"^\|\s*(\S+)\s*\|\s*(.+?)\s*\|\s*$")
_DATE_FORMAT = "%b %d %H:%M:%S %Y GMT"


def parse_expiry_table(lines):
    """
    Parse the ``--check-expiry`` table into a list of dicts:
    ``path``, ``expiration_date``, ``days_remaining`` (None if the date cannot
    be parsed) and ``expired``.
    """
    now = datetime.now(timezone.utc)
    certificates = []
    for line in lines:
        match = _TABLE_ROW.match(str(line).strip())
        if not match:
            continue
        path, date_str = match.groups()
        days_remaining = None
        expired = None
        try:
            expiry = datetime.strptime(date_str, _DATE_FORMAT).replace(tzinfo=timezone.utc)
            days_remaining = (expiry - now).days
            expired = expiry <= now
        except ValueError:
            pass
        certificates.append(
            dict(
                path=path,
                expiration_date=date_str,
                days_remaining=days_remaining,
                expired=expired,
            )
        )
    return certificates


def construct_command(params):
    """Build the powervc-opsmgr config certs command."""
    command = f"powervc-opsmgr config certs -c {params['cluster']}"

    if params.get("ca_cert"):
        command += f" --ca-cert {params['ca_cert']}"
    if params.get("ca_key"):
        command += f" --ca-key {params['ca_key']}"
    if params.get("copy"):
        command += " --copy"
    if params.get("rollback"):
        command += " --rollback"
    if params.get("validate"):
        command += " --validate"
        if params.get("chain"):
            command += " --chain"
    if params.get("cert_type"):
        command += f" --type {params['cert_type']}"

    sync = params.get("sync")
    if sync:
        command += " --sync" if sync == "default" else f" --sync {sync}"

    restart = params.get("restart")
    if restart:
        command += " --restart" if restart == "default" else f" --restart {restart}"

    check_expiry = params.get("check_expiry")
    if check_expiry:
        command += (
            " --check-expiry" if check_expiry == "default"
            else f" --check-expiry {check_expiry}"
        )

    if params.get("verbose"):
        command += " -v"

    return command


def run_cli_command():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            cluster=dict(type="str", required=True),
            ca_cert=dict(type="str"),
            ca_key=dict(type="str"),
            copy=dict(type="bool", default=False),
            rollback=dict(type="bool", default=False),
            validate=dict(type="bool", default=False),
            chain=dict(type="bool", default=False),
            cert_type=dict(
                type="str",
                choices=["rabbit", "zookeeper", "powervc", "novnc", "db", "memcached"],
            ),
            sync=dict(type="str", choices=["default", "secondary", "nl", "bn"]),
            restart=dict(type="str", choices=["default", "nl", "bn"]),
            check_expiry=dict(type="str", choices=["default", "nl", "bn"]),
            verbose=dict(type="bool", default=False),
        ),
    )

    try:
        p = module.params

        # ---------------- VALIDATION ----------------
        if not any(p.get(a) for a in ALL_ACTIONS):
            module.fail_json(
                changed=False,
                failed=True,
                msg=(
                    "At least one action must be specified: validate, copy, rollback, "
                    "cert_type, sync, restart or check_expiry."
                ),
            )

        if p.get("chain") and not p.get("validate"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="chain can only be used together with validate=true.",
            )

        if p.get("validate") and not p.get("ca_cert"):
            module.fail_json(
                changed=False,
                failed=True,
                msg="ca_cert is required when validate=true.",
            )

        command = construct_command(p)

        connection = Connection(
            module,
            p["login_host"],
            p["login_user"],
            p["login_password"],
            command=command,
            messages={},
        )

        rc, output = connection.run()

        # ---------------- NORMALIZE OUTPUT ----------------
        if isinstance(output, str):
            output = output.strip()
        output_list = output if isinstance(output, list) else [str(output)]
        rc = int(rc)

        # ---------------- TIMEOUT DETECTION ----------------
        timeout_detected = any("timed out" in str(line).lower() for line in output_list)
        if timeout_detected and "completed successfully" not in " ".join(output_list).lower():
            module.exit_json(
                changed=False,
                failed=False,
                warning=True,
                rc=rc,
                stdout_lines=output_list,
                msg="Operation timed out. Task may still be running on PowerVC.",
                error="",
            )

        # ---------------- RESULT ----------------
        failed = rc != 0
        changed = (not failed) and any(p.get(a) for a in MUTATING_ACTIONS)

        result = dict(
            changed=changed,
            failed=failed,
            warning=False,
            stdout_lines=output_list,
            error="",
            rc=rc,
            msg="",
        )

        if failed:
            error_lines = [
                str(line).strip()
                for line in output_list
                if "error" in str(line).lower()
            ]
            result["msg"] = (
                error_lines[0] if error_lines else "PowerVC certificate operation failed."
            )
            result["error"] = result["msg"]
        else:
            result["msg"] = "Certificate operation completed successfully"
            if p.get("check_expiry"):
                result["certificates"] = parse_expiry_table(output_list)

        module.exit_json(**result)

    except (CLIError, Exception) as e:
        module.fail_json(changed=False, failed=True, msg=str(e))


def main():
    run_cli_command()


if __name__ == "__main__":
    main()
