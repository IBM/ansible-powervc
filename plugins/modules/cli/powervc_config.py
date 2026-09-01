#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: powervc_config
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage identity repository configuration on PowerVC
description:
  - This module manages the identity repository settings on the PowerVC Controller
    via C(powervc-config identity repository) over SSH.
  - C(state=show) is read-only — displays current repository settings without making
    changes. Always returns C(changed=False).
  - C(state=present) configures the identity repository. When switching from C(os) to
    C(ldap) or modifying LDAP attributes, PowerVC services will be temporarily disrupted.
  - C(--quiet) mode (C(quiet=true)) suppresses interactive prompts and uses previously
    saved values for any unspecified settings. Only valid when C(repo_type) is specified.
  - C(user) and C(group) are mutually exclusive — only one may be specified to receive
    the initial admin role assignment.
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
      - C(show) — display current repository settings; read-only, always returns C(changed=False).
      - C(present) — configure the identity repository with the supplied options.
    required: true
    type: str
    choices: ['show', 'present']
  repo_type:
    description:
      - Type of identity repository to use.
      - C(os) — local OpenStack identity (Keystone).
      - C(ldap) — external LDAP/Active Directory.
    type: str
    choices: ['os', 'ldap']
  user:
    description:
      - Name of the user to be given the initial admin role assignment.
      - Mutually exclusive with C(group).
    type: str
  group:
    description:
      - Name of the group to be given the initial admin role assignment.
      - Mutually exclusive with C(user).
    type: str
  quiet:
    description:
      - Quiet mode — suppresses interactive prompts and uses previously saved
        values for any setting not explicitly specified.
      - Only valid when C(repo_type) is specified.
    type: bool
    default: false
  ldap_url:
    description:
      - URL of the LDAP server. Multiple servers for redundancy can be supplied
        as a comma-separated list.
    type: str
  anon:
    description:
      - If C(true), the LDAP bind will be anonymous.
    type: bool
    default: false
  chase_referrals:
    description:
      - Whether to chase LDAP referrals. Should be C(False) for Active Directory
        unless binding is anonymous.
    type: str
    choices: ['True', 'False']
  ldap_user:
    description:
      - User name for authenticating to the LDAP server,
        e.g. C(cn=bob,dc=example,dc=com).
    type: str
  tls_cert:
    description:
      - Path to the secure certificate file.
    type: str
  insecure:
    description:
      - If C(true), TLS will not be used to secure the LDAP connection.
    type: bool
    default: false
  tls_cacertfile:
    description:
      - Certificate authority certificate file for LDAP servers using TLS.
    type: str
  tls_cacertdir:
    description:
      - Certificate authority certificate directory for LDAP servers using TLS.
    type: str
  update_filters:
    description:
      - Interactively update LDAP user and group filters only.
        LDAP must already be enabled.
    type: bool
    default: false
  user_tree_dn:
    description:
      - Search base for users, e.g. C(ou=Users,dc=example,dc=com).
    type: str
  user_filter:
    description:
      - Search filter for users.
    type: str
  user_objectclass:
    description:
      - Object class for users, e.g. C(inetOrgPerson).
    type: str
  user_id_attr:
    description:
      - LDAP attribute for user IDs, e.g. C(uid).
    type: str
  user_name_attr:
    description:
      - LDAP attribute for user names, e.g. C(cn).
    type: str
  user_mail_attr:
    description:
      - LDAP attribute for user email addresses, e.g. C(email).
    type: str
  user_desc_attr:
    description:
      - LDAP attribute for user descriptions, e.g. C(description).
    type: str
  group_tree_dn:
    description:
      - Search base for groups, e.g. C(ou=Groups,dc=example,dc=com).
    type: str
  group_filter:
    description:
      - Search filter for groups.
    type: str
  group_objectclass:
    description:
      - Object class for groups, e.g. C(groupOfNames).
    type: str
  group_id_attr:
    description:
      - LDAP attribute for group IDs, e.g. C(cn).
    type: str
  group_name_attr:
    description:
      - LDAP attribute for group names, e.g. C(cn).
    type: str
  group_member_attr:
    description:
      - LDAP attribute for group members, e.g. C(member).
    type: str
  group_desc_attr:
    description:
      - LDAP attribute for group descriptions, e.g. C(description).
    type: str
  query_scope:
    description:
      - Scope for LDAP queries.
      - C(one) — one level below the search base.
      - C(sub) — entire subtree below the search base.
    type: str
    choices: ['one', 'sub']
notes:
  - Switching between C(os) and C(ldap) repositories or changing existing LDAP
    attributes will cause a temporary disruption of PowerVC service availability.
  - C(powervc-config identity debug) has been removed from the CLI. Use the
    C(powervc_log) module with C(service=identity) instead.
'''

EXAMPLES = '''
---
- name: Show current identity repository settings
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Display repository settings
      ibm.powervc.cli.powervc_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: show
      register: result
    - debug:
        var: result.stdout_lines


- name: Switch identity repository to LDAP
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Configure LDAP identity repository
      ibm.powervc.cli.powervc_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        repo_type: ldap
        quiet: true
        ldap_url: "{{ ldap_url }}"
        ldap_user: "{{ ldap_bind_user }}"
        user_tree_dn: "{{ ldap_user_tree_dn }}"
        group_tree_dn: "{{ ldap_group_tree_dn }}"
        chase_referrals: "False"
      register: result
    - debug:
        var: result.stdout_lines


- name: Switch identity repository back to local OS
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Set repository type to os
      ibm.powervc.cli.powervc_config:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        state: present
        repo_type: os
        quiet: true
      register: result
    - debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: >
    Whether a configuration change was made.
    C(false) for C(state=show) or when no options were supplied.
    C(true) for a successful C(state=present) mutation.
  returned: always
  type: bool
stdout_lines:
  description: Command output split into lines.
  returned: success
  type: list
  elements: str
rc:
  description: Return code from the remote command.
  returned: always
  type: int
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError


def _build_command(params):
    '''Build the powervc-config identity repository command from module params.

    state=show  → powervc-config identity repository   (no mutation flags)
    state=present → powervc-config identity repository [flags...]
    '''
    cmd = 'powervc-config identity repository'

    if params['state'] == 'show':
        return cmd, {}

    # --- optional flags ---
    if params.get('repo_type'):
        cmd += f" -t {params['repo_type']}"

    if params.get('user'):
        cmd += f" -u {params['user']}"

    if params.get('group'):
        cmd += f" -g {params['group']}"

    if params.get('quiet'):
        cmd += ' -q'

    if params.get('ldap_url'):
        cmd += f" --ldap-url {params['ldap_url']}"

    if params.get('anon'):
        cmd += ' --anon'

    if params.get('chase_referrals') is not None:
        cmd += f" --chase-referrals {params['chase_referrals']}"

    if params.get('ldap_user'):
        cmd += f" --ldap-user {params['ldap_user']}"

    if params.get('tls_cert'):
        cmd += f" --tls-cert {params['tls_cert']}"

    if params.get('insecure'):
        cmd += ' --insecure'

    if params.get('tls_cacertfile'):
        cmd += f" --tls-cacertfile {params['tls_cacertfile']}"

    if params.get('tls_cacertdir'):
        cmd += f" --tls-cacertdir {params['tls_cacertdir']}"

    if params.get('update_filters'):
        cmd += ' --update-filters'

    if params.get('user_tree_dn'):
        cmd += f" --user-tree-dn \"{params['user_tree_dn']}\""

    if params.get('user_filter'):
        cmd += f" --user-filter \"{params['user_filter']}\""

    if params.get('user_objectclass'):
        cmd += f" --user-objectclass {params['user_objectclass']}"

    if params.get('user_id_attr'):
        cmd += f" --user-id-attr {params['user_id_attr']}"

    if params.get('user_name_attr'):
        cmd += f" --user-name-attr {params['user_name_attr']}"

    if params.get('user_mail_attr'):
        cmd += f" --user-mail-attr {params['user_mail_attr']}"

    if params.get('user_desc_attr'):
        cmd += f" --user-desc-attr {params['user_desc_attr']}"

    if params.get('group_tree_dn'):
        cmd += f" --group-tree-dn \"{params['group_tree_dn']}\""

    if params.get('group_filter'):
        cmd += f" --group-filter \"{params['group_filter']}\""

    if params.get('group_objectclass'):
        cmd += f" --group-objectclass {params['group_objectclass']}"

    if params.get('group_id_attr'):
        cmd += f" --group-id-attr {params['group_id_attr']}"

    if params.get('group_name_attr'):
        cmd += f" --group-name-attr {params['group_name_attr']}"

    if params.get('group_member_attr'):
        cmd += f" --group-member-attr {params['group_member_attr']}"

    if params.get('group_desc_attr'):
        cmd += f" --group-desc-attr {params['group_desc_attr']}"

    if params.get('query_scope'):
        cmd += f" --query-scope {params['query_scope']}"

    # powervc-config identity repository prompts interactively unless -q is given.
    # When quiet=false and repo_type is specified the CLI may ask questions.
    # We do not auto-answer those — callers should set quiet=true for automation.
    messages = {}

    return cmd, messages


def run_powervc_config(module):
    p = module.params
    host = p['login_host']
    user = p['login_user']
    password = p['login_password']
    state = p['state']

    # Mutual exclusion: user and group cannot both be set
    if p.get('user') and p.get('group'):
        module.fail_json(
            changed=False,
            msg="'user' and 'group' are mutually exclusive — specify only one."
        )

    # quiet is only valid when repo_type is given
    if p.get('quiet') and not p.get('repo_type'):
        module.fail_json(
            changed=False,
            msg="'quiet' is only valid when 'repo_type' is specified."
        )

    cmd, messages = _build_command(p)

    if module.check_mode:
        module.exit_json(
            changed=(state == 'present'),
            rc=0,
            stdout_lines=[],
            msg=f"[CHECK MODE] Would run: {cmd}"
        )

    connection = Connection(module, host, user, password,
                            command=cmd, messages=messages)
    try:
        rc, output = connection.run()
    except (CLIError, Exception) as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        stderr_msg = '\n'.join(output) if isinstance(output, list) else str(output)
        module.fail_json(
            changed=False,
            rc=int(rc),
            msg=f"powervc-config command failed with rc={rc}",
            stderr=stderr_msg
        )

    lines = output if isinstance(output, list) else ([str(output)] if output else [])
    changed = (state == 'present')

    module.exit_json(
        changed=changed,
        rc=int(rc),
        stdout_lines=lines,
        msg="powervc-config identity repository completed successfully"
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            state=dict(type='str', required=True, choices=['show', 'present']),
            repo_type=dict(type='str', choices=['os', 'ldap']),
            user=dict(type='str'),
            group=dict(type='str'),
            quiet=dict(type='bool', default=False),
            ldap_url=dict(type='str'),
            anon=dict(type='bool', default=False),
            chase_referrals=dict(type='str', choices=['True', 'False']),
            ldap_user=dict(type='str'),
            tls_cert=dict(type='str'),
            insecure=dict(type='bool', default=False),
            tls_cacertfile=dict(type='str'),
            tls_cacertdir=dict(type='str'),
            update_filters=dict(type='bool', default=False),
            user_tree_dn=dict(type='str'),
            user_filter=dict(type='str'),
            user_objectclass=dict(type='str'),
            user_id_attr=dict(type='str'),
            user_name_attr=dict(type='str'),
            user_mail_attr=dict(type='str'),
            user_desc_attr=dict(type='str'),
            group_tree_dn=dict(type='str'),
            group_filter=dict(type='str'),
            group_objectclass=dict(type='str'),
            group_id_attr=dict(type='str'),
            group_name_attr=dict(type='str'),
            group_member_attr=dict(type='str'),
            group_desc_attr=dict(type='str'),
            query_scope=dict(type='str', choices=['one', 'sub']),
        ),
        mutually_exclusive=[['user', 'group']],
        supports_check_mode=True
    )

    run_powervc_config(module)


if __name__ == '__main__':
    main()
