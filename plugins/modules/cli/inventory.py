#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: inventory
author:
    - Yogita Garani (@yogita.garani1)
short_description: Manage PowerVC cluster inventory
description:
  - This module manages PowerVC cluster inventory operations over SSH.
  - C(state=list) displays current inventory — read-only, always returns C(changed=False).
  - C(state=present) creates a new cluster inventory using C(powervc-opsmgr inventory).
    Requires C(cluster), C(node_count), C(inventory_hosts), C(inventory_user),
    C(inventory_password), and C(virtual_ip) (Virtual IP/Hostname).
  - C(state=absent) deletes a cluster inventory. Requires C(cluster).
    When C(force=yes) the interactive confirmation prompt is answered C(y);
    when C(force=no) (default) the prompt is answered C(n) and no deletion occurs.
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
  state:
    description:
      - Operation to perform.
      - C(list) — display current inventory (read-only).
      - C(present) — create a new cluster inventory.
      - C(absent) — delete a cluster inventory.
    required: true
    type: str
    choices: ['list', 'present', 'absent']
  cluster:
    description:
      - Cluster name. Required for C(state=present) and C(state=absent).
        Optional for C(state=list) — when supplied, filters JSON output to
        that cluster (only used with C(json_format=yes)).
    type: str
  node_count:
    description:
      - Number of nodes in the PowerVC cluster.
        Required for C(state=present).
    type: int
  inventory_hosts:
    description:
      - List of IP addresses or hostnames of nodes in the cluster.
        The list length must match C(node_count).
        Required for C(state=present).
    type: list
    elements: str
  inventory_user:
    description:
      - Username used to access inventory nodes.
        Required for C(state=present).
    type: str
  inventory_password:
    description:
      - Password for the inventory user.
        Required for C(state=present).
    type: str
    no_log: true
  virtual_ip:
    description:
      - Virtual IP address or hostname for the cluster (answers the
        C(Enter Virtual IP/Hostname) interactive prompt).
        Required for C(state=present).
    type: str
  force:
    description:
      - When C(yes), answers the delete confirmation prompt with C(y) and
        proceeds with cluster deletion.
      - When C(no) (default), the confirmation is answered C(n) and the
        deletion does not occur.
    type: str
    required: false
    default: 'no'
    choices: ['yes', 'no']
  json_format:
    description:
      - When C(yes), output inventory listing in JSON format.
        Only used with C(state=list).
    type: str
    required: false
    default: 'no'
    choices: ['yes', 'no']
'''

EXAMPLES = '''
- name: "List inventory"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List all inventory"
      ibm.powervc.cli.inventory:
        state: list
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result
    - name: "Show output"
      debug:
        var: result.stdout_lines

- name: "List inventory in JSON format"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "List inventory as JSON"
      ibm.powervc.cli.inventory:
        state: list
        json_format: "yes"
        cluster: "{{ cluster_name }}"
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
      register: result
    - name: "Show output"
      debug:
        var: result.stdout_lines

- name: "Create inventory"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Create cluster inventory"
      ibm.powervc.cli.inventory:
        state: present
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        node_count: "{{ number_nodes }}"
        inventory_hosts: "{{ inventory_hosts }}"
        inventory_user: "{{ inventory_user }}"
        inventory_password: "{{ node_password }}"
        virtual_ip: "{{ virtual_ip }}"
      register: result
    - name: "Show output"
      debug:
        var: result.stdout_lines

- name: "Delete inventory"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Force delete cluster inventory"
      ibm.powervc.cli.inventory:
        state: absent
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
        force: "yes"
      register: result
    - name: "Show output"
      debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: Whether the inventory operation made a change.
  returned: always
  type: bool
rc:
  description: Return code from the remote command.
  returned: always
  type: int
stdout_lines:
  description: Command output split into a list of lines.
  returned: success
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
'''

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


def construct_command(state, cluster_name=None, number_nodes=None, virtual_ip=None,
                      node_ip=None, inventory_user=None, node_passwd=None,
                      force='no', json_format='no'):
    '''Construct the powervc-opsmgr inventory command and interactive messages.

    Returns (command, messages). Returns (None, {}) when required parameters
    are missing so the caller can fail with a descriptive error.
    '''
    messages = {}

    if state == 'list':
        if json_format == 'yes':
            command = "powervc-opsmgr inventory -j -l"
            if cluster_name is not None:
                command += f" -c {cluster_name}"
        else:
            command = "powervc-opsmgr inventory -l"
        return command, messages

    if state == 'present':
        if not all([cluster_name, number_nodes, virtual_ip, node_ip,
                    inventory_user, node_passwd]):
            return None, {}
        command = f"powervc-opsmgr inventory -c {cluster_name} --quiet"
        messages = {
            r"\s*Enter the number of nodes\s*:\s*": str(number_nodes),
        }
        for i in range(1, int(number_nodes) + 1):
            messages[rf"\s*Enter IP/Hostname for Node {i}\s*:\s*"] = node_ip[i - 1]
        messages.update({
            r"\s*Enter Username for all nodes\s*:\s*": inventory_user,
            r"\s*Enter Password for all nodes\s*:\s*": node_passwd,
            r"\s*Enter\s+Virtual\s+IP/Hostname\s*:\s*": virtual_ip,
        })
        return command, messages

    if state == 'absent':
        if cluster_name is None:
            return None, {}
        command = f"powervc-opsmgr inventory -c {cluster_name} -d"
        confirm = 'y' if force == 'yes' else 'n'
        messages = {
            r"(\s)*Are you sure you want to delete cluster (y/n)(\s)*:(\s)*": confirm
        }
        return command, messages

    return None, {}


def run_inventory(module):
    '''Execute the inventory command on the PowerVC Controller.'''
    state = module.params['state']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    cluster_name = module.params['cluster']
    number_nodes = module.params['node_count']
    node_ip = module.params['inventory_hosts']
    inventory_user = module.params['inventory_user']
    node_passwd = module.params['inventory_password']
    virtual_ip = module.params['virtual_ip']
    force = module.params['force']
    json_format = module.params['json_format']

    command, messages = construct_command(
        state, cluster_name, number_nodes, virtual_ip,
        node_ip, inventory_user, node_passwd, force, json_format
    )

    if command is None:
        module.fail_json(
            changed=False,
            msg="Missing required parameters for state='{}'. "
                "Check cluster, node_count, inventory_hosts, inventory_user, "
                "inventory_password, and virtual_ip.".format(state)
        )

    # check_mode: list is read-only (changed=False); present/absent would mutate
    if module.check_mode:
        module.exit_json(
            changed=(state != 'list'),
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host_ip, user, password,
                            command=command, messages=messages)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        lines = output if isinstance(output, list) else [str(output)]
        module.fail_json(
            msg="Inventory operation failed",
            rc=int(rc),
            stderr="\n".join(lines),
            changed=False
        )

    lines = output if isinstance(output, list) else [str(output)]

    # state=list is always read-only; state=absent with force=no answers 'n'
    # so the cluster is not actually deleted — report changed=False
    if state == 'list':
        changed = False
    elif state == 'absent' and force != 'yes':
        changed = False
    else:
        changed = True

    module.exit_json(
        changed=changed,
        rc=int(rc),
        stdout_lines=lines,
        msg="Inventory operation completed successfully"
    )


def main():
    '''Main execution'''
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=True,
                       choices=['list', 'present', 'absent']),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=False, default=None),
            node_count=dict(type='int', required=False, default=None),
            inventory_hosts=dict(type='list', elements='str',
                                 required=False, default=None),
            inventory_user=dict(type='str', required=False, default=None),
            inventory_password=dict(type='str', required=False,
                                    default=None, no_log=True),
            virtual_ip=dict(type='str', required=False, default=None),
            force=dict(type='str', required=False, default='no',
                       choices=['yes', 'no']),
            json_format=dict(type='str', required=False, default='no',
                             choices=['yes', 'no']),
        ),
        required_if=[
            ('state', 'present', ['cluster', 'node_count', 'inventory_hosts',
                                  'inventory_user', 'inventory_password', 'virtual_ip']),
            ('state', 'absent', ['cluster']),
        ],
        supports_check_mode=True
    )
    run_inventory(module)


if __name__ == '__main__':
    main()
