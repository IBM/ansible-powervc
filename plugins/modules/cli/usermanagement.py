#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: usermanagement
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC users
description:
  - This module creates, removes, modifies, and lists PowerVC users.
  - Creation and removal are idempotent — re-creating an existing user or removing
    a non-existent user returns C(changed=False).
  - C(action=modify_group) is idempotent — reads the user's current group via
    C(lspvcuser list) before acting; returns C(changed=False) if the group already
    matches the desired value.
  - C(action=update_expiry) is idempotent — reads the user's current expiry via
    C(lspvcuser list) before acting; returns C(changed=False) if the expiry already
    matches.
  - "B(Cluster scope behaviour — important):"
  - C(state=present) uses C(mkpvcuser create -c <cluster>) which propagates the new
    user B(to all nodes) in the cluster in a single operation.
  - C(state=absent) uses C(rmpvcuser -c <cluster>) and C(state=modify) uses
    C(chpvcuser -c <cluster>). Despite accepting the C(-c) cluster flag, both commands
    operate B(on the local node only) — the change B(does not propagate) to other nodes.
    These operations must be run B(separately against each node) in the cluster.
  - This is a B(PowerVC CLI design difference) between C(mkpvcuser) (cluster-wide) and
    C(chpvcuser)/C(rmpvcuser) (node-local). The module emits a warning at runtime for
    C(state=absent) and C(state=modify) to remind operators of this requirement.
  - "B(Password change restrictions on PowerVC (PVCVA) vs HMC):"
  - On B(HMC), any user holding the C(hmcsuperadmin) task role (or the
    C(ManageAllUserPasswords) task) can reset another locally-authenticated user's
    password. Kerberos user passwords can only be changed by the user themselves.
    LDAP user passwords cannot be changed via the HMC CLI at all.
  - On B(PowerVC (PVCVA)), this capability is B(more restricted) — only C(pvcroot)
    is permitted to reset another user's password via C(chpvcuser reset_passwd).
    Users with C(pvcsuperadmin) role cannot do this, unlike their HMC equivalent
    C(hmcsuperadmin). This is a known product inconsistency between IBM HMC and
    PowerVC.
  - C(action=ch_passwd) changes the B(authenticated SSH user's own) password only
    (C(login_user) must equal C(new_user)). It cannot set another user's password
    non-interactively regardless of the caller's role.
  - C(action=reset_passwd) resets B(another) user's password to the appliance
    default. Requires C(login_user=pvcroot). C(pvcsuperadmin) users are B(not)
    authorised to perform this action on PowerVC — unlike C(hmcsuperadmin) on HMC.
    No CLI flag exists to set a B(specific) password for another user
    non-interactively on PowerVC.
options:
  login_host:
    description:
      - IP address of the PowerVC Controller
    required: true
    type: str
  login_user:
    description:
      - SSH user (C(pvcroot))
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
      - Action to perform.
      - C(present) — Create user on B(all nodes) in the cluster (cluster-wide via C(mkpvcuser)).
      - C(absent) — Remove user. B(Node-local only) — must be run on each node separately.
      - C(show) — List users on the current node (read-only).
      - C(modify) — Modify user attributes. B(Node-local only) — must be run on each node separately.
    required: true
    type: str
    choices: ['present', 'absent', 'show', 'modify']
  new_user:
    description:
      - Username to create, remove, or modify
    type: str
  cluster:
    description:
      - Cluster name of PowerVC.
      - For C(state=present) this causes C(mkpvcuser) to create the user on B(all nodes)
        in the cluster.
      - For C(state=absent) and C(state=modify) the C(-c) flag provides cluster context
        to the CLI but the operation is B(node-local only) — it must be repeated on each
        node separately.
    type: str
  group:
    description:
      - Restricted shell group to add user to (C(pvcsuperadmin), C(pvcoperator), C(pvcviewer))
    type: str
  new_password:
    description:
      - Password for the new user or to change existing user password
      - Required for C(state=present) and C(action=ch_passwd)
      - Not required for C(action=reset_passwd) (resets to default password)
    type: str
    no_log: true
  expiry:
    description:
      - Expiry of user password (default 1 year, use C(10000) for never)
    type: str
  silent:
    description:
      - Silent mode for removal (no confirmation prompt)
    type: bool
    default: false
  confirm:
    description:
      - Confirmation string for removal
    type: str
  filter:
    description:
      - Filter for listing users (format C(key=value), e.g. C(name=root), C(uid=1000), C(groups=adm))
    type: str
  script:
    description:
      - Script mode for listing users (space-separated output)
    type: bool
    default: false
  fields:
    description:
      - Fields to display when listing users (C(name), C(uid), C(groups))
    type: str
  action:
    description:
      - Specific modify action.
      - "C(ch_passwd) — Change B(your own) password (requires C(new_password));
        C(login_user) must equal C(new_user). Cannot change another user's password
        regardless of role — this is a PowerVC CLI restriction."
      - "C(reset_passwd) — Reset B(another) user's password to the appliance default.
        Does not accept a specific new password. B(Requires C(login_user=pvcroot).)
        C(pvcsuperadmin) users cannot perform this action on PowerVC, unlike
        C(hmcsuperadmin) on HMC (known product inconsistency)."
      - C(modify_group) — Change user group (requires C(group)); idempotent.
      - C(update_expiry) — Update password expiry (requires C(expiry)); idempotent.
    type: str
    choices: ['ch_passwd', 'reset_passwd', 'modify_group', 'update_expiry']
'''

EXAMPLES = '''
- name: Create a PowerVC user
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Create user with group assignment
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        new_user: "{{ new_user }}"
        state: "present"
        cluster: "{{ cluster_name }}"
        group: "{{ group_name }}"
        new_password: "{{ pvcroot_password }}"
      register: result

    - name: Display create user output
      debug:
        var: result.stdout_lines


- name: Create a PowerVC user with password expiry
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Create user with expiry days
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        new_user: "{{ new_user }}"
        state: "present"
        cluster: "{{ cluster_name }}"
        group: "{{ group_name }}"
        new_password: "{{ pvcroot_password }}"
        expiry: "{{ expiry_days }}"
      register: result

    - name: Display create user with expiry output
      debug:
        var: result.stdout_lines


- name: Remove a PowerVC user
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove user with confirmation
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        new_user: "{{ new_user }}"
        state: "absent"
        cluster: "{{ cluster_name }}"
        silent: "{{ silent | bool }}"
        confirm: "yes"
      register: result

    - name: Display remove user output
      debug:
        var: result.stdout_lines


- name: List PowerVC users
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: List all users with filter
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        filter: "{{ lspvcuser_filter }}"
        script: "{{ lspvcuser_script | bool }}"
        fields: "{{ lspvcuser_fields }}"
      register: result

    - name: Display list users output
      debug:
        var: result.stdout_lines


- name: Change a PowerVC user password
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Change own password
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "modify"
        action: "ch_passwd"
        new_user: "{{ pvc_user }}"
        cluster: "{{ cluster_name }}"
        new_password: "{{ new_password }}"
      register: result

    - name: Display password change output
      debug:
        var: result.stdout_lines


- name: Modify a PowerVC user group
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Change user group assignment
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "modify"
        action: "modify_group"
        new_user: "{{ new_user }}"
        cluster: "{{ cluster_name }}"
        group: "{{ modify_group }}"
      register: result

    - name: Display group modify output
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether any user management changes were made
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string
  returned: always
  type: str
stdout_lines:
  description: Command output split into lines
  returned: always
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd, messages=None, check_idempotent=False, handle_errors=False):
    '''Run command via SSH connection'''
    conn = Connection(module, login_host, login_user,
                      login_password, command=cmd, messages=messages or {})
    rc, out = conn.run()

    # Handle idempotent cases
    if rc != 0 and check_idempotent:
        stderr_msg = "\n".join(out) if isinstance(out, list) else str(out)

        # Check for user already exists error
        if "User already exists" in stderr_msg or "Cannot recreate same user" in stderr_msg:
            return stderr_msg, out, True  # Return with idempotent flag

        # Check for user not found error
        if "User not found" in stderr_msg or "does not exist" in stderr_msg or "No such user" in stderr_msg:
            return stderr_msg, out, True  # Return with idempotent flag

    if rc != 0 and handle_errors:
        stderr_msg = "\n".join(out) if isinstance(out, list) else str(out)

        error_patterns = [
            "doesnot exists",
            "does not exist",
            "Group '.*' doesnot exists",
            "Invalid group",
            "Permission denied",
            "not authorized",
            "Invalid expiry"
        ]

        for pattern in error_patterns:
            if pattern.lower() in stderr_msg.lower():
                return stderr_msg, out, True

        # Any other non-zero rc with handle_errors — treat as soft error
        return stderr_msg, out, True

    if rc != 0:
        # Convert list to string for stderr
        stderr_msg = "\n".join(out) if isinstance(out, list) else str(out)
        module.fail_json(msg=f"Command failed: {cmd}", stderr=stderr_msg)

    if isinstance(out, list):
        return "\n".join(out), out, False

    return out, out, False


def result_ok(lines, changed=False):
    return {
        "changed": changed,
        "stdout": "\n".join(lines) if isinstance(lines, list) else lines,
        "stdout_lines": lines if isinstance(lines, list) else [lines]
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


def handle_present(module, login_host, login_user, login_password, new_user, cluster, group, new_password, expiry):
    '''Create a new PowerVC user'''
    if not new_user:
        module.fail_json(msg="new_user is required for creating a user")
    if not cluster:
        module.fail_json(msg="cluster is required for creating a user")
    if not new_password:
        module.fail_json(msg="new_password is required for creating a user")

    # Build command
    cmd = f"mkpvcuser create -u {new_user} -c {cluster}"

    if group:
        cmd += f" -g {group}"

    if expiry:
        cmd += f" -e {expiry}"

    if module.check_mode:
        return result_ok([f"[CHECK MODE] Would create user {new_user}"], changed=True)

    # Use messages dict to handle password prompts
    messages = {
        "Enter new password.*:": new_password,
        "Confirm password:": new_password
    }

    _, lines, is_idempotent = run_cmd(
        module, login_host, login_user, login_password, cmd, messages, check_idempotent=True)
    cleaned = clean_output(lines)

    # If user already exists, return success with changed=False
    if is_idempotent:
        return result_ok(cleaned if cleaned else [f"User {new_user} already exists"], changed=False)

    return result_ok(cleaned if cleaned else [f"User {new_user} created successfully"], changed=True)


def handle_absent(module, login_host, login_user, login_password, new_user, cluster, silent, confirm):
    '''Remove a PowerVC user'''
    if not new_user:
        module.fail_json(msg="new_user is required for removing a user")
    if not cluster:
        module.fail_json(msg="cluster is required for removing a user")

    # Warn: rmpvcuser is node-local — does not propagate across the cluster
    module.warn(
        f"state=absent (rmpvcuser) is node-local on PowerVC. "
        f"Removing user '{new_user}' on this node only. "
        f"Repeat this task against each node in cluster '{cluster}' separately."
    )

    # Build command
    cmd = f"rmpvcuser -u {new_user} -c {cluster}"

    if module.check_mode:
        return result_ok([f"[CHECK MODE] Would remove user {new_user} (node-local)"], changed=True)

    # Handle silent mode or interactive confirmation
    messages = {}

    if silent:
        # Silent mode - use -s flag, no prompts
        cmd += " -s"
    else:
        # Use caller-supplied confirm value if provided, otherwise default to "yes"
        confirm_answer = confirm if confirm else "yes"
        messages = {
            r".*\(yes/no\).*": confirm_answer,
            r".*yes/no.*": confirm_answer
        }

    _, lines, is_idempotent = run_cmd(
        module, login_host, login_user, login_password, cmd, messages, check_idempotent=True)
    cleaned = clean_output(lines)

    # If user doesn't exist, return success with changed=False
    if is_idempotent:
        return result_ok(cleaned if cleaned else [f"User {new_user} does not exist"], changed=False)

    return result_ok(cleaned if cleaned else [f"User {new_user} removed successfully"], changed=True)


def handle_show(module, login_host, login_user, login_password, filter_val, script, fields):
    '''List PowerVC users'''
    cmd = "lspvcuser list"

    if filter_val:
        cmd += f" --filter {filter_val}"

    if script:
        cmd += " --script"

    if fields:
        cmd += f" --fields {fields}"

    _, lines, _ = run_cmd(module, login_host, login_user, login_password, cmd)
    cleaned = clean_output(lines)

    return result_ok(cleaned if cleaned else ["No users found"], changed=False)


def _read_user_field(module, login_host, login_user, login_password, new_user, field):
    '''Read a single field for a user via lspvcuser list.

    Returns the stripped field value string, or None if the command fails or
    the user cannot be found — callers treat None as "skip idempotency check".
    Uses handle_errors=True so a non-zero rc is returned as an error flag
    rather than calling fail_json.
    '''
    cmd = f"lspvcuser list --filter name={new_user} --fields {field} --script"
    _, lines, is_error = run_cmd(module, login_host, login_user, login_password,
                                 cmd, handle_errors=True)
    if is_error:
        return None
    for line in lines:
        line = line.strip()
        if line and not line.startswith("+") and not line.lower().startswith(field):
            return line
    return None


def handle_modify(module, login_host, login_user, login_password, new_user, cluster, group, new_password, expiry, action):
    '''Modify a PowerVC user (change password, group, or expiry)'''
    if not new_user:
        module.fail_json(msg="user is required")
    if not cluster:
        module.fail_json(msg="cluster is required")

    # Warn: chpvcuser is node-local — does not propagate across the cluster
    module.warn(
        f"state=modify (chpvcuser) is node-local on PowerVC. "
        f"Modifying user '{new_user}' on this node only. "
        f"Repeat this task against each node in cluster '{cluster}' separately."
    )

    if action == "ch_passwd" and login_user != new_user:
        msg = (
            f"Skipped: ch_passwd can only change the authenticated user's own password "
            f"(login_user='{login_user}', new_user='{new_user}'). "
            f"PowerVC does not allow non-interactive password changes for other users "
            f"regardless of role. To reset another user's password to the appliance "
            f"default, use action='reset_passwd' with login_user='pvcroot'."
        )
        return result_ok([msg], changed=False)

    if action == "reset_passwd" and login_user == new_user:
        msg = (
            "Skipped: reset_passwd resets another user's password, not your own. "
            "To change your own password use action='ch_passwd'."
        )
        return result_ok([msg], changed=False)

    if action == "reset_passwd" and login_user != "pvcroot":
        module.warn(
            f"reset_passwd requires pvcroot privileges on PowerVC (PVCVA). "
            f"Current login_user is '{login_user}'. Unlike HMC where hmcsuperadmin "
            f"can reset other users' passwords, pvcsuperadmin cannot do this on "
            f"PowerVC — only pvcroot is authorised. This operation may fail."
        )

    # Validate required parameters for each action
    if action == "modify_group" and not group:
        module.fail_json(msg="group is required for action 'modify_group'")

    if action == "update_expiry" and not expiry:
        module.fail_json(msg="expiry is required for action 'update_expiry'")

    # Only ch_passwd requires new_password; reset_passwd resets to default password
    if action == "ch_passwd" and not new_password:
        module.fail_json(msg="new_password is required for action 'ch_passwd'")

    # Idempotency: read current state before mutating
    if action == "modify_group":
        current_group = _read_user_field(
            module, login_host, login_user, login_password, new_user, "groups")
        if current_group is not None and group.lower() in current_group.lower():
            return result_ok(
                [f"User {new_user} already in group '{group}' — no change required"],
                changed=False
            )

    if action == "update_expiry":
        current_expiry = _read_user_field(
            module, login_host, login_user, login_password, new_user, "expiry")
        if current_expiry is not None and current_expiry.strip() == str(expiry).strip():
            return result_ok(
                [f"User {new_user} expiry already '{expiry}' — no change required"],
                changed=False
            )

    if module.check_mode:
        return result_ok([f"[CHECK MODE] Would perform {action} on user {new_user}"], changed=True)

    cmd = f"chpvcuser {action} -u {new_user} -c {cluster}"

    if action == "modify_group":
        cmd += f" -g {group}"
    elif action == "update_expiry":
        cmd += f" -e {expiry}"

    messages = {}
    if action == "ch_passwd":
        messages = {
            r"Enter new password.*:\s*": new_password,
            r"Confirm.*password.*:\s*": new_password
        }

    _, lines, is_error = run_cmd(module, login_host, login_user, login_password,
                                 cmd, messages if messages else None, handle_errors=True)
    cleaned = clean_output(lines)

    if is_error:
        return result_ok(cleaned if cleaned else [f"Error modifying user {new_user}"], changed=False)

    return result_ok(cleaned if cleaned else [f"User {new_user} modified successfully"], changed=True)


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type="str", required=True),
            login_user=dict(type="str", required=True),
            login_password=dict(type="str", required=True, no_log=True),
            state=dict(type="str", required=True, choices=[
                       "present", "absent", "show", "modify"]),
            new_user=dict(type="str"),
            cluster=dict(type="str"),
            group=dict(type="str"),
            new_password=dict(type="str", no_log=True),
            expiry=dict(type="str"),
            silent=dict(type="bool", default=False),
            confirm=dict(type="str"),
            filter=dict(type="str"),
            script=dict(type="bool", default=False),
            fields=dict(type="str"),
            action=dict(type="str", choices=[
                        "ch_passwd", "reset_passwd", "modify_group", "update_expiry"])
        ),
        required_if=[
            ("state", "present", ["new_user", "cluster", "new_password"]),
            ("state", "absent", ["new_user", "cluster"]),
            ("state", "modify", ["new_user", "cluster", "action"])
        ],
        supports_check_mode=True
    )

    login_host = module.params["login_host"]
    login_user = module.params["login_user"]
    login_password = module.params["login_password"]
    state = module.params["state"]
    new_user = module.params.get("new_user")
    cluster = module.params.get("cluster")
    group = module.params.get("group")
    new_password = module.params.get("new_password")
    expiry = module.params.get("expiry")
    silent = module.params.get("silent", False)
    confirm = module.params.get("confirm")
    filter_val = module.params.get("filter")
    script = module.params.get("script", False)
    fields = module.params.get("fields")
    action = module.params.get("action")

    if state == "present":
        result = handle_present(module, login_host, login_user,
                                login_password, new_user, cluster, group, new_password, expiry)
    elif state == "absent":
        result = handle_absent(module, login_host, login_user,
                               login_password, new_user, cluster, silent, confirm)
    elif state == "show":
        result = handle_show(module, login_host, login_user,
                             login_password, filter_val, script, fields)
    elif state == "modify":
        result = handle_modify(module, login_host, login_user, login_password,
                               new_user, cluster, group, new_password, expiry, action)
    else:
        module.fail_json(msg="Invalid state")

    module.exit_json(**result)


if __name__ == "__main__":
    main()
