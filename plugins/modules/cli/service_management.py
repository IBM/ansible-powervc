#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: service_management
author:
    - Fredolin B Brone (@Fredolin-B-Brone1)
short_description: Manage PowerVC services on the Controller
description:
  - This module manages PowerVC services on the Controller over SSH using
    the C(powervc-services) CLI tool.
  - The command structure follows C(powervc-services [service] operation [flags]).
  - C(operation=status) is read-only and always returns C(changed=False).
  - C(operation=start), C(stop), C(restart), C(enable), C(disable) return C(changed=True).
  - C(operation=list) is only valid when C(service=remote) and is read-only.
  - C(enable) and C(disable) cannot be used with a specific C(service) subset and
    can only be run on a management node.
  - C(advanced) takes a value of C(component), C(node), or an inventory hostname
    (from C(powervc-opsmgr inventory -l)), and is only valid with C(operation=restart).
  - C(local=yes) restricts the operation to the management node only (C(--local) flag).
  - C(node) is only valid when C(service=remote); use C(all) or a specific node name
    from C(powervc-services remote list).
  - C(output_format) applies to C(operation=status) only.
  - C(live=yes) forces a live status refresh instead of returning cached data.
    Only valid with C(operation=status) on controller nodes.
  - C(refresh_cache) manages automatic cached-status refresh (C(enable), C(disable),
    C(status)). Only valid with C(operation=status) on controller nodes.
  - C(interval) sets the refresh interval in minutes for C(refresh_cache=enable).
    Minimum is 3, default is 10. Only valid with C(refresh_cache=enable).
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
      - Password for the SSH user
    required: true
    type: str
    no_log: true
  operation:
    description:
      - Operation to perform on the services.
      - C(status) — display service status (read-only).
      - C(start) — start services.
      - C(stop) — stop services.
      - C(restart) — restart services.
      - C(enable) — enable services (management node only, no C(service) subset).
      - C(disable) — disable services (management node only, no C(service) subset).
      - C(list) — list remote nodes. Only valid when C(service=remote).
    required: true
    type: str
    choices: ['status', 'start', 'stop', 'restart', 'enable', 'disable', 'list']
  service:
    description:
      - Service subset to target. When omitted all services are targeted.
      - C(remote) enables remote-node operations (C(list), C(restart --node), etc.).
    required: false
    type: str
    choices: ['db', 'rabbitmq', 'httpd', 'ego', 'glance', 'zookeeper', 'cinder',
              'neutron', 'nova', 'ceilometer', 'health', 'gnocchi', 'bumblebee',
              'ui-server', 'blazar', 'panko', 'swift', 'clerk', 'validator',
              'squall', 'placement', 'remote', 'all']
  node:
    description:
      - Remote node to target. Valid values are C(all) or a specific node name
        from C(powervc-services remote list). Only valid when C(service=remote).
    required: false
    type: str
  local:
    description:
      - When C(yes), restrict the operation to the management node only
        (passes C(--local) flag).
    required: false
    type: str
    default: 'no'
    choices: ['yes', 'no']
  advanced:
    description:
      - Advanced restart mode. Only valid with C(operation=restart).
      - C(component) — rolling restart component by component across all nodes.
      - C(node) — restart all services on one node before moving to the next.
      - An inventory hostname from C(powervc-opsmgr inventory -l) — host-specific restart.
    required: false
    type: str
  skip:
    description:
      - One or more components to skip. Only valid with C(operation=start),
        C(stop), or C(restart). Separate multiple values with spaces.
    required: false
    type: str
  output_format:
    description:
      - Output format for C(operation=status).
      - C(json) — machine-readable JSON output (C(--json) flag).
      - C(raw) — string representation format (C(--raw) flag).
      - C(detail) — detailed output including RabbitMQ cluster status (C(--detail) flag).
    required: false
    type: str
    choices: ['json', 'raw', 'detail']
  live:
    description:
      - When C(yes), return the latest live service status instead of cached data
        (passes C(--live) flag). Only valid with C(operation=status) on controller nodes.
    required: false
    type: str
    default: 'no'
    choices: ['yes', 'no']
  refresh_cache:
    description:
      - Manage automatic cached-status refresh (passes C(--refresh-cache) flag).
        Only valid with C(operation=status) on controller nodes.
      - C(enable) — enable automatic refresh.
      - C(disable) — disable automatic refresh.
      - C(status) — show current refresh configuration.
    required: false
    type: str
    choices: ['enable', 'disable', 'status']
  interval:
    description:
      - Refresh interval in minutes for C(refresh_cache=enable).
        Minimum is 3, default is 10. Only valid with C(refresh_cache=enable).
    required: false
    type: int
'''

EXAMPLES = '''
- name: "Show local service status"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Show status of all local services"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "status"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Show remote service status"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Show status of remote services"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "status"
        service: "remote"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "List remote nodes"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List remote nodes"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "list"
        service: "remote"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Restart a specific service"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Restart nova service"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "restart"
        service: "nova"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Advanced restart"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Perform advanced component restart"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "restart"
        advanced: "component"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Restart services on a specific remote node"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Restart all services on a specific node"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "restart"
        service: "remote"
        node: "{{ node }}"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Restart services skipping a component"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Restart services, skip nova"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "restart"
        skip: "{{ skip }}"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines

- name: "Get service status in JSON format"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Get service status as JSON"
      ibm.powervc.cli.service_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        operation: "status"
        output_format: "json"
      register: result
    - name: "Show command output"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether a service state change was made. Always C(False) for C(operation=status) and C(operation=list).
  returned: always
  type: bool
stdout:
  description: Raw command output as a single string.
  returned: always
  type: str
stdout_lines:
  description: Command output split into a list of lines.
  returned: always
  type: list
  elements: str
'''

from ansible.module_utils.basic import AnsibleModule
from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection

# Operations that are read-only — never report changed=True
_READ_ONLY_OPS = frozenset(['status', 'list'])


def build_command(operation, service=None, node=None, local='no', advanced=None,
                  skip=None, output_format=None, live='no',
                  refresh_cache=None, interval=None):
    '''Build the powervc-services command string from the given parameters.

    Syntax: powervc-services [service_subset] operation [flags]
    '''
    parts = ["powervc-services"]

    # service subset comes before the operation (positional argument)
    if service:
        parts.append(service)

    parts.append(operation)

    # --- flags ---
    if local == 'yes':
        parts.append("--local")
    if node:
        parts.extend(["--node", node])
    if advanced and operation == 'restart':
        parts.extend(["--advanced", advanced])
    if skip and operation in ('start', 'stop', 'restart'):
        parts.extend(["--skip", skip])

    # output_format flags (status only)
    if output_format and operation == 'status':
        if output_format == 'json':
            parts.append("--json")
        elif output_format == 'raw':
            parts.append("--raw")
        elif output_format == 'detail':
            parts.append("--detail")

    if live == 'yes' and operation == 'status':
        parts.append("--live")
    if refresh_cache and operation == 'status':
        parts.extend(["--refresh-cache", refresh_cache])
        if refresh_cache == 'enable' and interval is not None:
            parts.extend(["--interval", str(interval)])

    return " ".join(parts)


def run_service_management(module):
    '''Execute the service management command on the PowerVC Controller.'''
    host = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    operation = module.params['operation']
    service = module.params.get('service')
    node = module.params.get('node')
    local = module.params.get('local', 'no')
    advanced = module.params.get('advanced')
    skip = module.params.get('skip')
    output_format = module.params.get('output_format')
    live = module.params.get('live', 'no')
    refresh_cache = module.params.get('refresh_cache')
    interval = module.params.get('interval')

    command = build_command(operation, service, node, local, advanced,
                            skip, output_format, live, refresh_cache, interval)

    changed = operation not in _READ_ONLY_OPS

    if module.check_mode:
        module.exit_json(
            changed=changed,
            stdout="",
            stdout_lines=[],
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host, user, password, command=command)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(msg=str(e), changed=False)

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(
            msg=f"Service management command failed: {command}",
            rc=int(rc),
            stderr=stderr_msg,
            changed=False
        )

    lines = output if isinstance(output, list) else [str(output)]

    module.exit_json(
        changed=changed,
        stdout="\n".join(lines),
        stdout_lines=lines
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            operation=dict(type='str', required=True,
                           choices=['status', 'start', 'stop', 'restart',
                                    'enable', 'disable', 'list']),
            service=dict(type='str', required=False,
                         choices=['db', 'rabbitmq', 'httpd', 'ego', 'glance',
                                  'zookeeper', 'cinder', 'neutron', 'nova',
                                  'ceilometer', 'health', 'gnocchi', 'bumblebee',
                                  'ui-server', 'blazar', 'panko', 'swift', 'clerk',
                                  'validator', 'squall', 'placement', 'remote', 'all']),
            node=dict(type='str', required=False),
            local=dict(type='str', required=False, default='no',
                       choices=['yes', 'no']),
            advanced=dict(type='str', required=False),
            skip=dict(type='str', required=False),
            output_format=dict(type='str', required=False,
                               choices=['json', 'raw', 'detail']),
            live=dict(type='str', required=False, default='no',
                      choices=['yes', 'no']),
            refresh_cache=dict(type='str', required=False,
                               choices=['enable', 'disable', 'status']),
            interval=dict(type='int', required=False),
        ),
        supports_check_mode=True
    )

    run_service_management(module)


if __name__ == '__main__':
    main()
