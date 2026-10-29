#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: openstack_commands
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage OpenStack role assignments for LDAP users and groups on PowerVC
description:
  - This module maps LDAP users or groups to OpenStack/PowerVC roles and projects
    by running C(openstack role add) and C(openstack role remove) commands on the
    PowerVC Controller over SSH.
  - All OpenStack CLI calls supply the required OpenStack environment variables
    (C(OS_AUTH_URL), C(OS_USERNAME), C(OS_PASSWORD), etc.) via the SSH channel
    C(env) request (Paramiko C(update_environment)) — variables are injected at
    the SSH protocol level, completely bypassing the remote login shell.  No
    shell sourcing, C(export) statements, or absolute command paths are used,
    so the module is fully compatible with C(rbash).
  - C(state=present) is B(idempotent). Before adding a role the module checks whether
    the assignment already exists via C(openstack role assignment list). If the
    assignment is already present it returns C(changed=False) without running
    C(openstack role add).
  - C(state=absent) is B(idempotent). The module checks whether the assignment
    exists before running C(openstack role remove). If it does not exist it returns
    C(changed=False).
  - C(state=list) displays all role assignments for the supplied C(project). Always
    returns C(changed=False).
  - Either C(ldap_user) or C(ldap_group) must be specified — but not both.
  - When C(all_projects=true), C(state=present) or C(state=absent) applies the role
    mapping to every project on the system, skipping the C(powervm), C(service), and
    C(ibm-default) projects (matching the behavior of the reference shell loop).
    C(project) is ignored when C(all_projects=true).
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
    no_log: true
  os_username:
    description:
      - OpenStack username for running the C(openstack) CLI commands.
        Typically C(servicebroker) or C(pvcroot).
    required: true
    type: str
  os_password:
    description:
      - Password for C(os_username). Passed via environment variable so it
        never appears on the command line.
    required: true
    type: str
    no_log: true
  os_auth_url:
    description:
      - Full Keystone endpoint, e.g. C(https://9.47.64.53:5000/v3).
      - When omitted, derived automatically as C(https://<login_host>:5000/v3).
    type: str
  os_project:
    description:
      - OpenStack project scope for the authentication token.
      - Use C(service) for C(servicebroker) (the default) or the target
        project name (e.g. C(ibm-default)) for C(pvcroot).
    type: str
    default: service
  os_user_domain_name:
    description:
      - Keystone user domain name. Defaults to C(Default).
    type: str
    default: Default
  os_project_domain_name:
    description:
      - Keystone project domain name. Defaults to C(Default).
    type: str
    default: Default
  os_identity_api_version:
    description:
      - Keystone API version. Defaults to C(3).
    type: str
    default: '3'
  state:
    description:
      - C(present) — ensure the role assignment exists (idempotent).
      - C(absent)  — ensure the role assignment does not exist (idempotent).
      - C(list)    — list role assignments for the project; read-only.
    required: true
    type: str
    choices: ['present', 'absent', 'list']
  role:
    description:
      - OpenStack role to assign, e.g. C(admin), C(viewer), C(member).
      - Required for C(state=present) and C(state=absent).
    type: str
  project:
    description:
      - OpenStack project to assign the role in.
      - Required for C(state=present), C(state=absent), and C(state=list)
        unless C(all_projects=true).
    type: str
  ldap_user:
    description:
      - LDAP user to assign/remove the role for.
      - Mutually exclusive with C(ldap_group).
    type: str
  ldap_group:
    description:
      - LDAP group to assign/remove the role for.
      - Mutually exclusive with C(ldap_user).
    type: str
  all_projects:
    description:
      - When C(true), apply the role mapping to every non-infrastructure project
        on the system (i.e. all projects except those containing C(powervm),
        C(service), or with name C(ibm-default)).
      - When C(true), the C(project) parameter is ignored.
      - Only valid for C(state=present) and C(state=absent).
    type: bool
    default: false
notes:
  - The module injects C(OS_AUTH_URL), C(OS_USERNAME), C(OS_PASSWORD),
    C(OS_PROJECT_NAME), C(OS_USER_DOMAIN_NAME), C(OS_PROJECT_DOMAIN_NAME),
    and C(OS_IDENTITY_API_VERSION) directly into the command string so they
    reach the C(openstack) process regardless of C(sshd) C(AcceptEnv) settings.
    Supply any of the C(os_auth_url), C(os_project), C(os_user_domain_name),
    C(os_project_domain_name), or C(os_identity_api_version) parameters to
    override the defaults. Every C(openstack) call also carries C(--insecure)
    to handle PowerVC's self-signed TLS certificate.
  - Role assignments in OpenStack are additive — assigning a role that already
    exists produces no error but the module detects this via
    C(openstack role assignment list) and avoids issuing a redundant
    C(openstack role add).
  - The C(openstack) CLI must be available on the PowerVC Controller
    (it is installed by default on all PowerVC appliances).
'''

EXAMPLES = '''
---
- name: Assign LDAP group pvcadmin to admin role in ibm-default project
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Map pvcadmin group to admin role in ibm-default
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: present
        role: admin
        project: ibm-default
        ldap_group: pvcadmin
      register: result
    - debug:
        var: result.stdout_lines


- name: Assign LDAP group pvcadmin to admin role in all tenant projects
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Map pvcadmin group to admin role across all projects
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: present
        role: admin
        ldap_group: pvcadmin
        all_projects: true
      register: result
    - debug:
        var: result.stdout_lines


- name: Assign LDAP group pvcview to viewer role in ibm-default project
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Map pvcview group to viewer role in ibm-default
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: present
        role: viewer
        project: ibm-default
        ldap_group: pvcview
      register: result
    - debug:
        var: result.stdout_lines


- name: Assign a specific LDAP user to the admin role in a project
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Map ldapuser1 to admin role
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: present
        role: admin
        project: ibm-default
        ldap_user: ldapuser1
      register: result
    - debug:
        var: result.stdout_lines


- name: Remove an LDAP group role assignment
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove pvcadmin group admin role from ibm-default
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: absent
        role: admin
        project: ibm-default
        ldap_group: pvcadmin
      register: result
    - debug:
        var: result.stdout_lines


- name: List role assignments for a project
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Show assignments for ibm-default
      ibm.powervc.cli.openstack_commands:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        os_username: "{{ os_username }}"
        os_password: "{{ os_password }}"
        state: list
        project: ibm-default
      register: result
    - debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: >
    Whether any role assignment change was made.
    C(false) for C(state=list) or when the assignment was already in the
    desired state. C(true) when one or more assignments were added or removed.
  returned: always
  type: bool
stdout_lines:
  description: Command output split into lines.
  returned: success
  type: list
  elements: str
rc:
  description: Return code of the last OpenStack CLI command executed.
  returned: always
  type: int
msg:
  description: Human-readable status message.
  returned: always
  type: str
projects_changed:
  description: >
    List of project names on which the role was actually added or removed.
    Only populated when C(all_projects=true).
  returned: when all_projects is true
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection

# Infrastructure project names to exclude when all_projects=true.
# Matches the reference shell-loop logic:
#   grep -v powervm | grep -v service | grep -v ID | awk '{print $2}'
# ibm-default is handled separately (explicit first call in the reference script).
_SKIP_PROJECTS = frozenset({'powervm', 'service'})


def _os_env_dict(os_auth_url, os_username, os_password, os_project,
                 os_user_domain_name, os_project_domain_name,
                 os_identity_api_version):
    '''Return a dict of OpenStack env vars to prepend to the command string.

    All values are caller-supplied; no defaults are applied here.
    ``PYTHONHTTPSVERIFY=0`` disables Python TLS verification for the
    self-signed PowerVC certificate.
    '''
    return {
        'OS_AUTH_URL': os_auth_url,
        'OS_USERNAME': os_username,
        'OS_PASSWORD': os_password,
        'OS_PROJECT_NAME': os_project,
        'OS_USER_DOMAIN_NAME': os_user_domain_name,
        'OS_PROJECT_DOMAIN_NAME': os_project_domain_name,
        'OS_IDENTITY_API_VERSION': os_identity_api_version,
        'PYTHONHTTPSVERIFY': '0',
    }


def _wrap(openstack_cmd):
    '''Append ``--insecure`` to an openstack CLI command string.

    The OpenStack env vars are passed separately via the SSH channel
    ``env`` parameter — no shell preamble is required here.
    ``--insecure`` disables TLS certificate verification for PowerVC's
    self-signed certificate.
    '''
    return f"{openstack_cmd} --insecure"


def _run(module, host, user, password, cmd, env=None):
    '''Execute cmd over SSH with optional channel-level env vars.'''
    conn = Connection(module, host, user, password, command=cmd, env=env)
    rc, out = conn.run()
    lines = out if isinstance(out, list) else (out.splitlines() if out else [])
    return int(rc), lines


def _assignment_exists(module, host, user, password,
                       env_args, role, project, ldap_user, ldap_group):
    '''Return True when the role assignment already exists.

    Uses ``openstack role assignment list`` scoped to the given project,
    role, and user/group.  A non-zero rc or empty output means "not found".
    '''
    subject_flag = (f"--user '{ldap_user}'" if ldap_user
                    else f"--group '{ldap_group}'")
    query = (
        f"openstack role assignment list "
        f"--project '{project}' --role '{role}' "
        f"{subject_flag} -f value"
    )
    env = _os_env_dict(*env_args)
    rc, lines = _run(module, host, user, password, _wrap(query), env=env)
    if rc != 0:
        return False
    # Any non-empty, non-header output means the assignment is present.
    return any(line.strip() for line in lines)


def _list_tenant_projects(module, host, user, password, env_args):
    '''Return project names, excluding infrastructure ones.

    Mirrors the reference shell loop:
        for project in $(openstack project list | grep -v powervm |
                         grep -v service | grep -v ID | awk '{print $2}')
    Returns a list of project name strings.
    '''
    env = _os_env_dict(*env_args)
    cmd = _wrap("openstack project list -f value -c Name")
    rc, lines = _run(module, host, user, password, cmd, env=env)
    if rc != 0:
        return []
    projects = []
    for line in lines:
        name = line.strip()
        if not name:
            continue
        # Skip infrastructure projects (case-insensitive substring match)
        if any(skip in name.lower() for skip in _SKIP_PROJECTS):
            continue
        projects.append(name)
    return projects


def _handle_single(module, host, user, password,
                   env_args, state, role, project, ldap_user, ldap_group,
                   check_mode):
    '''Add or remove a single role assignment.

    Returns (changed, rc, lines, msg).
    '''
    subject_flag = (f"--user '{ldap_user}'" if ldap_user
                    else f"--group '{ldap_group}'")
    subject_label = ldap_user or ldap_group

    exists = _assignment_exists(module, host, user, password,
                                env_args, role, project, ldap_user, ldap_group)

    env = _os_env_dict(*env_args)

    if state == 'present':
        if exists:
            return (False, 0, [],
                    f"Role '{role}' already assigned to '{subject_label}' "
                    f"in project '{project}' — no change required")

        action_cmd = (
            f"openstack role add --project '{project}' "
            f"{subject_flag} '{role}'"
        )
        if check_mode:
            return (True, 0, [],
                    f"[CHECK MODE] Would run: {action_cmd}")

        rc, lines = _run(module, host, user, password, _wrap(action_cmd), env=env)
        if rc != 0:
            return (False, rc, lines,
                    f"openstack role add failed for project '{project}' rc={rc}")
        return (True, rc, lines,
                f"Role '{role}' assigned to '{subject_label}' "
                f"in project '{project}'")

    else:  # absent
        if not exists:
            return (False, 0, [],
                    f"Role '{role}' not assigned to '{subject_label}' "
                    f"in project '{project}' — no change required")

        action_cmd = (
            f"openstack role remove --project '{project}' "
            f"{subject_flag} '{role}'"
        )
        if check_mode:
            return (True, 0, [],
                    f"[CHECK MODE] Would run: {action_cmd}")

        rc, lines = _run(module, host, user, password, _wrap(action_cmd), env=env)
        if rc != 0:
            return (False, rc, lines,
                    f"openstack role remove failed for project '{project}' rc={rc}")
        return (True, rc, lines,
                f"Role '{role}' removed from '{subject_label}' "
                f"in project '{project}'")


def run_openstack_commands(module):
    p = module.params
    host = p['login_host']
    user = p['login_user']
    password = p['login_password']
    state = p['state']
    role = p.get('role')
    project = p.get('project')
    ldap_user = p.get('ldap_user')
    ldap_group = p.get('ldap_group')
    all_projects = p.get('all_projects', False)

    # Resolve OpenStack env values — user-supplied wins, otherwise default.
    os_auth_url = p['os_auth_url'] or f"https://{host}:5000/v3"
    env_args = (
        os_auth_url,
        p['os_username'],
        p['os_password'],
        p['os_project'],
        p['os_user_domain_name'],
        p['os_project_domain_name'],
        p['os_identity_api_version'],
    )

    # --- Parameter validation ---
    if state in ('present', 'absent'):
        if not role:
            module.fail_json(changed=False,
                             msg="'role' is required for state='%s'" % state)
        if not ldap_user and not ldap_group:
            module.fail_json(changed=False,
                             msg="One of 'ldap_user' or 'ldap_group' must be specified.")
        if not all_projects and not project:
            module.fail_json(changed=False,
                             msg="'project' is required when 'all_projects' is false.")

    if state == 'list' and not project:
        module.fail_json(changed=False,
                         msg="'project' is required for state='list'.")

    # --- state=list ---
    if state == 'list':
        env = _os_env_dict(*env_args)
        cmd = _wrap(f"openstack role assignment list --project '{project}'")
        rc, lines = _run(module, host, user, password, cmd, env=env)
        if rc != 0:
            err = '\n'.join(lines)
            module.fail_json(changed=False, rc=rc,
                             msg=f"openstack role assignment list failed rc={rc}",
                             stderr=err)
        module.exit_json(
            changed=False,
            rc=rc,
            stdout_lines=lines,
            msg=f"Role assignments for project '{project}' listed successfully"
        )

    # --- state=present / state=absent, all_projects=false ---
    if not all_projects:
        changed, rc, lines, msg = _handle_single(
            module, host, user, password,
            env_args, state, role, project, ldap_user, ldap_group,
            module.check_mode
        )
        if rc != 0:
            module.fail_json(changed=False, rc=rc, stdout_lines=lines, msg=msg)
        module.exit_json(changed=changed, rc=rc, stdout_lines=lines, msg=msg)

    # --- state=present / state=absent, all_projects=true ---
    projects = _list_tenant_projects(module, host, user, password, env_args)
    if not projects:
        module.exit_json(
            changed=False, rc=0, stdout_lines=[],
            projects_changed=[],
            msg="No tenant projects found — no role assignments changed"
        )

    all_lines = []
    projects_changed = []
    last_rc = 0

    for proj in projects:
        changed_p, rc_p, lines_p, msg_p = _handle_single(
            module, host, user, password,
            env_args, state, role, proj, ldap_user, ldap_group,
            module.check_mode
        )
        all_lines.append(f"[{proj}] {msg_p}")
        all_lines.extend(lines_p)
        last_rc = max(last_rc, rc_p)
        if changed_p:
            projects_changed.append(proj)
        if rc_p != 0:
            # Non-fatal: log and continue so remaining projects are processed.
            module.warn(f"Role mapping failed for project '{proj}': {msg_p}")

    module.exit_json(
        changed=bool(projects_changed),
        rc=last_rc,
        stdout_lines=all_lines,
        projects_changed=projects_changed,
        msg=(f"Role mapping applied across {len(projects)} projects; "
             f"{len(projects_changed)} changed")
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            os_username=dict(type='str', required=True),
            os_password=dict(type='str', required=True, no_log=True),
            os_auth_url=dict(type='str', default=None),
            os_project=dict(type='str', default='service'),
            os_user_domain_name=dict(type='str', default='Default'),
            os_project_domain_name=dict(type='str', default='Default'),
            os_identity_api_version=dict(type='str', default='3'),
            state=dict(type='str', required=True,
                       choices=['present', 'absent', 'list']),
            role=dict(type='str'),
            project=dict(type='str'),
            ldap_user=dict(type='str'),
            ldap_group=dict(type='str'),
            all_projects=dict(type='bool', default=False),
        ),
        mutually_exclusive=[['ldap_user', 'ldap_group']],
        supports_check_mode=True
    )

    run_openstack_commands(module)


if __name__ == '__main__':
    main()
