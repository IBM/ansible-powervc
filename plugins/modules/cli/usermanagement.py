#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: usermanagement
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC users
description:
  - This module creates, removes, modifies, and lists PowerVC users
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
      - Action to perform (present to create, absent to remove, show to list, modify to change)
    required: true
    type: str
    choices: ['present', 'absent', 'show', 'modify']
  new_user:
    description:
      - Username to create, remove, or modify
    type: str
  cluster:
    description:
      - Cluster name of PowerVC
    type: str
  group:
    description:
      - Restricted shell group user should be added to (pvcsuperadmin, pvcoperator, pvcviewer)
    type: str
  new_password:
    description:
      - Password for the new user or to change existing user password
      - Required for state=present and action=ch_passwd
      - Not required for action=reset_passwd (resets to default password)
    type: str
  expiry:
    description:
      - Expiry of user password (default 1 year, 10000 for never)
    type: str
  silent:
    description:
      - Silent mode for removal (no confirmation)
    type: bool
    default: false
  confirm:
    description:
      - Confirmation string for removal
    type: str
  filter:
    description:
      - Filter for listing users (format key=value, e.g., name=root, uid=1000, groups=adm)
    type: str
  script:
    description:
      - Script mode for listing users (space-separated output)
    type: bool
    default: false
  fields:
    description:
      - Fields to display when listing users (name, uid, groups)
    type: str
  action:
    description:
      - Specific modify action
      - ch_passwd - Change your own password (requires new_password)
      - reset_passwd - Reset another user's password to default (no new_password needed)
      - modify_group - Change user's group (requires group)
      - update_expiry - Update password expiry (requires expiry)
    type: str
    choices: ['ch_passwd', 'reset_passwd', 'modify_group', 'update_expiry']
"""

EXAMPLE = """
---
- name: Create a PowerVC user
  hosts: localhost

  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Create a user"
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

    - name: "Show create user output"
      debug:
        var: result.stdout_lines


    - name: "Create a user with password expiry"
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

    - name: "Show create user with expiry output"
      debug:
        var: result.stdout_lines

---
- name: Remove a PowerVC user
  hosts: localhost

  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Remove a user"
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

    - name: "Show remove user output"
      debug:
        var: result.stdout_lines

---
- name: List PowerVC users
  hosts: localhost

  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: Lists user information.
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        filter: "{{ lspvcuser_filter }}"
        script: "{{ lspvcuser_script | bool }}"
        fields: "{{ lspvcuser_fields }}"
      register: result

    - name: "Show list users output"
      debug:
        var: result.stdout_lines


    - name: Lists user information.
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        filter: "{{ filter_list }}"
      register: result

    - name: "Show filtered users output"
      debug:
        var: result.stdout_lines


    - name: Lists user information in scripts.
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        script: true
      register: result

    - name: "Show script mode output"
      debug:
        var: result.stdout_lines


    - name: Lists user information with field value.
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "show"
        script: true
        fields: "name"
      register: result

    - name: "Show field-specific output"
      debug:
        var: result.stdout_lines

---
- name: Chnage a PowerVC user password
  hosts: localhost

  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Change user password"
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

    - name: "Show password change output"
      debug:
        var: result.stdout_lines


    - name: "Reset another user's password to default"
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "modify"
        action: "reset_passwd"
        new_user: "{{ new_user }}"
        cluster: "{{ cluster_name }}"
      register: result

    - name: "Show reset password output"
      debug:
        var: result.stdout_lines


    - name: "Update password expiry"
      ibm.powervc.cli.usermanagement:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: "modify"
        action: "update_expiry"
        new_user: "{{ new_user }}"
        cluster: "{{ cluster_name }}"
        expiry: "{{ expiry_days }}"
      register: result

    - name: "Show expiry update output"
      debug:
        var: result.stdout_lines

---
- name: Modify a PowerVC user group
  hosts: localhost

  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Modify user group"
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

    - name: "Show output"
      debug:
        var: result.stdout_lines

"""
from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection


def run_cmd(module, login_host, login_user, login_password, cmd, messages=None, check_idempotent=False, handle_errors=False):
    """Run command via SSH connection"""
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
    """Create a new PowerVC user"""
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
    """Remove a PowerVC user"""
    if not new_user:
        module.fail_json(msg="new_user is required for removing a user")
    if not cluster:
        module.fail_json(msg="cluster is required for removing a user")

    # Build command
    cmd = f"rmpvcuser -u {new_user} -c {cluster}"

    # Handle silent mode or interactive confirmation
    messages = {}

    if silent:
        # Silent mode - use -s flag, no prompts
        cmd += " -s"
    else:
        # Not silent - handle the confirmation prompt with "yes"
        messages = {
            r".*\(yes/no\).*": "yes",
            r".*yes/no.*": "yes"
        }

    _, lines, is_idempotent = run_cmd(
        module, login_host, login_user, login_password, cmd, messages, check_idempotent=True)
    cleaned = clean_output(lines)

    # If user doesn't exist, return success with changed=False
    if is_idempotent:
        return result_ok(cleaned if cleaned else [f"User {new_user} does not exist"], changed=False)

    return result_ok(cleaned if cleaned else [f"User {new_user} removed successfully"], changed=True)


def handle_show(module, login_host, login_user, login_password, filter_val, script, fields):
    """List PowerVC users"""
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


def handle_modify(module, login_host, login_user, login_password, new_user, cluster, group, new_password, expiry, action):
    """Modify a PowerVC user (change password or group)"""
    if not new_user:
        module.fail_json(msg="user is required")
    if not cluster:
        module.fail_json(msg="cluster is required")

    if action == "ch_passwd" and login_user != new_user:
        msg = (
            f"Skipped: ch_passwd can only be used to change your own password. "
            f"Current user: '{login_user}', Target user: '{new_user}'. "
            f"To change another user's password, use action='reset_passwd' (requires pvcroot privileges)."
        )
        return result_ok([msg], changed=False)

    if action == "reset_passwd" and login_user == new_user:
        msg = (
            "Skipped: reset_passwd is for changing another user's password. "
            "To change your own password, use action='ch_passwd'."
        )
        return result_ok([msg], changed=False)

    # Validate required parameters for each action
    if action == "modify_group" and not group:
        module.fail_json(msg="group is required for action 'modify_group'")

    if action == "update_expiry" and not expiry:
        module.fail_json(msg="expiry is required for action 'update_expiry'")

    # Only ch_passwd requires new_password; reset_passwd resets to default password
    if action == "ch_passwd" and not new_password:
        module.fail_json(msg="new_password is required for action 'ch_passwd'")

    cmd = f"chpvcuser {action} -u {new_user} -c {cluster}"

    if action == "modify_group":
        cmd += f" -g {group}"
    elif action == "update_expiry":
        cmd += f" -e {expiry}"

    messages = {}
    if action == "ch_passwd":
        # Only ch_passwd prompts for password; reset_passwd resets to default automatically
        # Match the exact prompts from chpvcuser command:
        # "Enter new password for 'username': " and "Confirm new password: "
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
        supports_check_mode=False
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
