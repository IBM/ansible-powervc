#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: network_management
author:
    - Yogita Garani (@yogita.garani1)
short_description: Manage network configuration on PowerVC Controller
description:
  - This module manages network configuration on the PowerVC Controller over SSH.
  - Supports firewall rules (C(component=firewall)), network routes
    (C(component=route)), network interfaces (C(component=network)), DNS
    settings (C(component=dns)), NTP service management (C(component=ntp)),
    and hosts-file management (C(component=update_dns)).
  - C(state=show) is read-only and always returns C(changed=False).
  - C(component=network) does not support C(state=absent); C(chpvc network) has
    no remove subcommand — use C(component=firewall), C(route), or C(dns) for
    removal operations.
  - C(component=network) is idempotent — C(state=present) and C(state=modify) read
    C(chpvc network show --interface) first and skip the command if all supplied
    fields (IP, netmask, gateway) already match. C(--check) mode also reads current state.
  - C(component=network), C(state=modify) automatically answers the interactive
    confirmation prompt with C(yes).
  - C(component=dns) is idempotent — C(state=present) reads C(chpvc network_dns show)
    first and skips the add if the entry already exists; C(state=absent) skips the
    remove if the entry is already absent. C(--check) mode also reads current state.
  - C(component=ntp), C(state=show) maps to C(chpvc ntp status) and is read-only.
  - C(component=ntp), C(state=present) maps to C(chpvc ntp enable).
  - C(component=ntp), C(state=absent) maps to C(chpvc ntp disable).
  - C(component=ntp), C(action=set) sets NTP servers via C(chpvc ntp set).
  - C(component=ntp), C(action=unset) removes NTP servers via C(chpvc ntp unset).
  - C(component=ntp), C(action=restart) restarts chronyd via C(chpvc ntp restart).
  - C(component=update_dns) manages C(/etc/hosts) entries via C(chpvc update_dns).
  - C(component=update_dns), C(state=show) displays current hosts-file entries.
  - C(component=update_dns), C(state=present) adds an entry (C(entry) required);
    idempotent — skips if the entry already exists.
  - C(component=update_dns), C(state=absent) removes an entry (C(entry) required);
    idempotent — skips if the entry is already absent.
  - C(component=update_dns), C(state=modify) replaces an existing entry
    (both C(entry) and C(new_entry) required); always mutates.
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
  component:
    description:
      - Network component to manage.
      - C(firewall) — manage firewall allow/deny rules via C(chpvc firewall).
      - C(route) — manage static network routes via C(chpvc netroute).
      - C(network) — manage network interfaces via C(chpvc network)
        (C(present), C(modify), C(show) only — no C(absent)).
      - C(dns) — manage DNS servers and domain suffixes via C(chpvc network_dns).
      - C(ntp) — manage NTP service and servers via C(chpvc ntp).
      - C(update_dns) — manage C(/etc/hosts) entries via C(chpvc update_dns).
    required: true
    type: str
    choices: ['firewall', 'route', 'network', 'dns', 'ntp', 'update_dns']
  state:
    description:
      - Desired operation to perform.
      - C(present) — add or allow; for C(ntp) enables chronyd.
      - C(absent) — remove or deny; for C(ntp) disables chronyd.
      - C(modify) — modify interface settings (C(network) only).
      - C(show) — display current settings; read-only, always returns C(changed=False).
        For C(ntp) maps to C(chpvc ntp status).
    required: true
    type: str
    choices: ['present', 'absent', 'modify', 'show']
  action:
    description:
      - Sub-action for C(component=ntp).
      - C(set) — set NTP servers (requires C(ntp_servers) or C(ntp_trust_servers)).
      - C(unset) — remove NTP servers (requires C(ntp_servers)).
      - C(restart) — restart the chronyd service.
      - When not specified the C(state) value drives the operation.
    required: false
    type: str
    choices: ['set', 'unset', 'restart']
  ntp_servers:
    description:
      - Comma-separated list of NTP server addresses.
      - Used with C(action=set) (maps to C(--servers)) and
        C(action=unset) (maps to C(--servers)).
    required: false
    type: str
  ntp_trust_servers:
    description:
      - Comma-separated list of trusted NTP server addresses.
      - Used with C(action=set) only (maps to C(--trust-servers)).
    required: false
    type: str
  address:
    description:
      - IP address for the network component.
      - Required for C(component=firewall) and C(component=route).
    required: false
    type: str
  netmask:
    description:
      - Network mask (maps to C(-nm) flag).
    required: false
    type: str
  interface:
    description:
      - Network interface name (e.g. C(eth0)).
      - Required for C(component=network), C(state=present).
    required: false
    type: str
  gateway:
    description:
      - Gateway IP address.
    required: false
    type: str
  position:
    description:
      - Position for a route table entry (maps to C(--position) flag).
    required: false
    type: str
  route_type:
    description:
      - Type of route. Required for C(component=route).
    required: false
    type: str
    choices: ['host', 'net']
  dns_server:
    description:
      - DNS server IP address (maps to C(--dns-server) flag).
    required: false
    type: str
  domain_suffix:
    description:
      - Domain suffix for DNS search list (maps to C(--domain-suffix) flag).
    required: false
    type: str
  entry:
    description:
      - Hosts-file entry string for C(component=update_dns).
      - For C(state=present) and C(state=absent) this is the full entry to add
        or remove (e.g. C(192.168.1.10 myhost.example.com myhost)).
      - For C(state=modify) this is the existing entry to replace (C(--old_entry)).
    required: false
    type: str
  new_entry:
    description:
      - Replacement hosts-file entry for C(component=update_dns), C(state=modify).
        Maps to C(--new_entry).
    required: false
    type: str
'''

EXAMPLES = '''
- name: Add a network route
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Add host route
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: route
        state: present
        route_type: host
        address: "{{ address }}"
        netmask: "{{ netmask }}"
        gateway: "{{ gateway }}"
        interface: "{{ interface }}"
        position: "{{ position }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Remove a network route
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove host route
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: route
        state: absent
        route_type: host
        address: "{{ address }}"
        netmask: "{{ netmask }}"
        gateway: "{{ gateway }}"
        interface: "{{ interface }}"
        position: "{{ position }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Add a network interface
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Add network interface
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: network
        state: present
        interface: "{{ interface }}"
        address: "{{ address }}"
        netmask: "{{ netmask }}"
        gateway: "{{ gateway }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Show network interface information
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Show interface
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: network
        state: show
        interface: "{{ interface }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Add DNS configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Add DNS server
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: dns
        state: present
        dns_server: "{{ dns_server }}"
        domain_suffix: "{{ domain_suffix }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Remove DNS configuration
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove DNS server
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: dns
        state: absent
        dns_server: "{{ dns_server }}"
        domain_suffix: "{{ domain_suffix }}"
      register: result
    - debug:
        var: result.stdout_lines
- name: Show NTP status
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Show NTP service status
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: ntp
        state: show
      register: result
    - debug:
        var: result.stdout_lines


- name: Enable NTP
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Enable and start chronyd
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: ntp
        state: present
      register: result
    - debug:
        var: result.stdout_lines


- name: Set NTP servers
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Set NTP servers
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: ntp
        state: present
        action: set
        ntp_servers: "{{ ntp_servers }}"
        ntp_trust_servers: "{{ ntp_trust_servers }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Unset NTP servers
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Unset specific NTP servers
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: ntp
        state: absent
        action: unset
        ntp_servers: "{{ ntp_servers }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Disable NTP
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Disable and stop chronyd
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: ntp
        state: absent
      register: result
    - debug:
        var: result.stdout_lines


- name: Show hosts-file entries
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Display current /etc/hosts entries
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: update_dns
        state: show
      register: result
    - debug:
        var: result.stdout_lines


- name: Add a hosts-file entry
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Add entry to /etc/hosts
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: update_dns
        state: present
        entry: "{{ hosts_entry }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Remove a hosts-file entry
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Remove entry from /etc/hosts
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: update_dns
        state: absent
        entry: "{{ hosts_entry }}"
      register: result
    - debug:
        var: result.stdout_lines


- name: Modify a hosts-file entry
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Replace an existing /etc/hosts entry
      ibm.powervc.cli.network_management:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        component: update_dns
        state: modify
        entry: "{{ hosts_entry }}"
        new_entry: "{{ new_hosts_entry }}"
      register: result
    - debug:
        var: result.stdout_lines
'''

RETURN = '''
changed:
  description: >
    Whether a network change was made.
    C(false) for C(state=show) (read-only) and on failure.
    C(true) for all mutating operations that succeed.
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

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_firewall_command(state, address, netmask=None, interface=None):
    '''Construct the chpvc firewall command.'''
    if state == 'present':
        command = f"chpvc firewall add -a {address}"
    elif state == 'absent':
        command = f"chpvc firewall remove -a {address}"
    else:
        return None
    if netmask is not None:
        command += f" -nm {netmask}"
    if interface is not None:
        command += f" -i {interface}"
    return command


def construct_netroute_command(state, route_type, address, netmask=None,
                               gateway=None, interface=None, position=None):
    '''Construct the chpvc netroute command.'''
    if state == 'present':
        command = f"chpvc netroute add --routetype {route_type} -a {address}"
    elif state == 'absent':
        command = f"chpvc netroute remove --routetype {route_type} -a {address}"
    else:
        return None
    if netmask is not None:
        command += f" -nm {netmask}"
    if gateway is not None:
        command += f" -g {gateway}"
    if interface is not None:
        command += f" -i {interface}"
    if position is not None:
        command += f" --position {position}"
    return command


def construct_network_command(state, interface=None, address=None,
                              netmask=None, gateway=None):
    '''Construct the chpvc network command. state=absent is not supported.'''
    if state == 'present':
        command = (f"chpvc network add --interface {interface} "
                   f"--ip {address} --netmask {netmask}")
        if gateway is not None:
            command += f" --gateway {gateway}"
    elif state == 'modify':
        command = "chpvc network modify"
        if interface is not None:
            command += f" --interface {interface}"
        if address is not None:
            command += f" --ip {address}"
        if netmask is not None:
            command += f" --netmask {netmask}"
        if gateway is not None:
            command += f" --gateway {gateway}"
    elif state == 'show':
        command = "chpvc network show"
        if interface is not None:
            command += f" --interface {interface}"
    else:
        # absent not supported for network component
        return None
    return command


def construct_ntp_command(state, action=None, ntp_servers=None,
                          ntp_trust_servers=None):
    '''Construct the chpvc ntp command.

    Mapping:
      state=show                      → chpvc ntp status
      state=present  (no action)      → chpvc ntp enable
      state=absent   (no action)      → chpvc ntp disable
      state=present, action=set       → chpvc ntp set [--servers ...] [--trust-servers ...]
      state=absent,  action=unset     → chpvc ntp unset [--servers ...]
      state=present, action=restart   → chpvc ntp restart
    '''
    if state == 'show':
        return "chpvc ntp status"

    if action == 'restart':
        return "chpvc ntp restart"

    if action == 'set':
        command = "chpvc ntp set"
        if ntp_servers is not None:
            command += f" --servers {ntp_servers}"
        if ntp_trust_servers is not None:
            command += f" --trust-servers {ntp_trust_servers}"
        return command

    if action == 'unset':
        command = "chpvc ntp unset"
        if ntp_servers is not None:
            command += f" --servers {ntp_servers}"
        return command

    # plain enable / disable
    if state == 'present':
        return "chpvc ntp enable"
    if state == 'absent':
        return "chpvc ntp disable"

    return None


def construct_update_dns_command(state, entry=None, new_entry=None):
    '''Construct the chpvc update_dns command.

    Mapping:
      state=show                          → chpvc update_dns show
      state=present  (entry required)     → chpvc update_dns add --entry ENTRY
      state=absent   (entry required)     → chpvc update_dns remove --entry ENTRY
      state=modify   (entry + new_entry)  → chpvc update_dns modify
                                               --old_entry ENTRY --new_entry NEW_ENTRY
    '''
    if state == 'show':
        return "chpvc update_dns show"
    if state == 'present':
        if entry is None:
            return None
        return f'chpvc update_dns add --entry "{entry}"'
    if state == 'absent':
        if entry is None:
            return None
        return f'chpvc update_dns remove --entry "{entry}"'
    if state == 'modify':
        if entry is None or new_entry is None:
            return None
        return f'chpvc update_dns modify --old_entry "{entry}" --new_entry "{new_entry}"'
    return None


def _read_update_dns_current(module, host_ip, user, password):
    '''Read current /etc/hosts entries via chpvc update_dns show.

    Returns a set of normalised (stripped, lowercased) entry strings.
    Returns None on failure so callers skip idempotency rather than aborting.
    '''
    connection = Connection(module, host_ip, user, password,
                            command="chpvc update_dns show", messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None

    if int(rc) != 0:
        return None

    lines = output if isinstance(output, list) else str(output).splitlines()
    entries = set()
    for line in lines:
        line = line.strip()
        if line and not line.startswith('+') and not line.startswith('#'):
            entries.add(line.lower())
    return entries


def _update_dns_entry_exists(current_entries, entry):
    '''Return True if entry (lowercased) is present in current_entries.'''
    if current_entries is None:
        return False
    return entry.strip().lower() in current_entries


def _parse_network_show(lines):
    '''Parse output of ``chpvc network show`` into a dict of field → value.

    Expected output contains lines like:
        IP Address  : 10.0.0.5
        Netmask     : 255.255.255.0
        Gateway     : 10.0.0.1

    Returns a dict with lowercase-stripped values for keys
    ``ip``, ``netmask``, ``gateway``.  Missing fields are absent from the dict.
    Returns an empty dict if lines is empty or unparseable.
    '''
    result = {}
    field_map = {
        'ip address': 'ip',
        'ip': 'ip',
        'netmask': 'netmask',
        'gateway': 'gateway',
    }
    for line in lines:
        if ':' not in line:
            continue
        key, _, val = line.partition(':')
        key = key.strip().lower()
        val = val.strip().lower()
        if not val:
            continue
        for pattern, canonical in field_map.items():
            if key.startswith(pattern):
                result[canonical] = val
                break
    return result


def _read_network_current(module, host_ip, user, password, interface):
    '''Read current interface config via ``chpvc network show --interface``.

    Returns a dict with keys ``ip``, ``netmask``, ``gateway`` (subset present
    in the output).  Returns None on any failure so callers skip idempotency
    rather than aborting.
    '''
    if not interface:
        return None
    cmd = f"chpvc network show --interface {interface}"
    connection = Connection(module, host_ip, user, password,
                            command=cmd, messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None

    if int(rc) != 0:
        return None

    lines = output if isinstance(output, list) else str(output).splitlines()
    parsed = _parse_network_show(lines)
    return parsed if parsed else None


def _network_already_matches(current, address=None, netmask=None, gateway=None):
    '''Return True if every supplied field already matches the current config.

    Only fields explicitly provided (not None) are compared.
    Returns False if current is None (idempotency skipped).
    '''
    if current is None:
        return False
    if address is not None and current.get('ip') != address.strip().lower():
        return False
    if netmask is not None and current.get('netmask') != netmask.strip().lower():
        return False
    if gateway is not None and current.get('gateway') != gateway.strip().lower():
        return False
    return True


def construct_dns_command(state, dns_server=None, domain_suffix=None):
    '''Construct the chpvc network_dns command.'''
    if state == 'present':
        command = "chpvc network_dns add"
    elif state == 'absent':
        command = "chpvc network_dns remove"
    elif state == 'show':
        return "chpvc network_dns show"
    else:
        return None
    if dns_server is not None:
        command += f" --dns-server {dns_server}"
    if domain_suffix is not None:
        command += f" --domain-suffix {domain_suffix}"
    return command


def _read_dns_current(module, host_ip, user, password):
    '''Read current DNS servers and domain suffixes via chpvc network_dns show.

    Returns (servers, suffixes) where each is a set of lowercase strings.
    If the show command fails, returns (None, None) so the caller proceeds
    without idempotency rather than aborting.
    '''
    connection = Connection(module, host_ip, user, password,
                            command="chpvc network_dns show", messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None, None

    if int(rc) != 0:
        return None, None

    lines = output if isinstance(output, list) else str(output).splitlines()
    servers = set()
    suffixes = set()
    for line in lines:
        line = line.strip()
        # typical output lines: "DNS Server: 8.8.8.8" / "Domain Suffix: example.com"
        if line.lower().startswith("dns server"):
            val = line.split(":", 1)[-1].strip().lower()
            if val:
                servers.add(val)
        elif line.lower().startswith("domain suffix"):
            val = line.split(":", 1)[-1].strip().lower()
            if val:
                suffixes.add(val)
    return servers, suffixes


def _dns_already_present(current_servers, current_suffixes, dns_server, domain_suffix):
    '''Return True if every requested entry already exists in current state.'''
    if current_servers is None:
        return False
    if dns_server and dns_server.lower() not in current_servers:
        return False
    if domain_suffix and domain_suffix.lower() not in current_suffixes:
        return False
    return True


def _dns_already_absent(current_servers, current_suffixes, dns_server, domain_suffix):
    '''Return True if every requested entry is already absent from current state.'''
    if current_servers is None:
        return False
    if dns_server and dns_server.lower() in current_servers:
        return False
    if domain_suffix and domain_suffix.lower() in current_suffixes:
        return False
    return True


# Interactive confirmation prompt emitted by `chpvc network modify`.
_NETWORK_MODIFY_PROMPT = r"Do you want to proceed\? \(yes/no\):"


def construct_command(state, component, address=None, netmask=None,
                      interface=None, gateway=None, position=None,
                      route_type=None, dns_server=None, domain_suffix=None,
                      action=None, ntp_servers=None, ntp_trust_servers=None,
                      entry=None, new_entry=None):
    '''Return (command, messages) or (None, {error: ...}) on invalid combination.'''
    messages = {}
    if component == 'firewall':
        command = construct_firewall_command(state, address, netmask, interface)
    elif component == 'route':
        command = construct_netroute_command(
            state, route_type, address, netmask, gateway, interface, position)
    elif component == 'network':
        if state == 'absent':
            return None, {'error': "component 'network' does not support state 'absent'"}
        command = construct_network_command(state, interface, address, netmask, gateway)
        if state == 'modify':
            messages = {_NETWORK_MODIFY_PROMPT: 'yes'}
    elif component == 'dns':
        command = construct_dns_command(state, dns_server, domain_suffix)
    elif component == 'ntp':
        command = construct_ntp_command(state, action, ntp_servers, ntp_trust_servers)
    elif component == 'update_dns':
        command = construct_update_dns_command(state, entry, new_entry)
        if command is None and state != 'show':
            return None, {'error': (
                f"component 'update_dns' state='{state}' requires 'entry'"
                + (" and 'new_entry'" if state == 'modify' else "")
            )}
    else:
        command = None
    return command, messages


# Phrases that appear in stdout when chpvc reports a logical failure despite
# returning rc=0.  Verified from live output: the ERROR box is always present
# and the surrounding decorators are consistent across firmware versions.
_STDOUT_ERROR_PHRASES = (
    "\x1b[1m \x1b[4merror\x1b[0m",   # ANSI-decorated ERROR heading
    "verify if the correct active network interface",  # known error body text
)


def _stdout_has_error(lines):
    '''Return True if any line in output contains a known failure phrase.'''
    joined = "\n".join(lines).lower()
    return any(phrase.lower() in joined for phrase in _STDOUT_ERROR_PHRASES)


def run_network_management(module):
    '''Execute the network management command on the PowerVC Controller.'''
    state = module.params['state']
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    component = module.params['component']
    address = module.params['address']
    netmask = module.params['netmask']
    interface = module.params['interface']
    gateway = module.params['gateway']
    position = module.params['position']
    route_type = module.params['route_type']
    dns_server = module.params['dns_server']
    domain_suffix = module.params['domain_suffix']
    action = module.params.get('action')
    ntp_servers = module.params.get('ntp_servers')
    ntp_trust_servers = module.params.get('ntp_trust_servers')
    entry = module.params.get('entry')
    new_entry = module.params.get('new_entry')

    # network idempotency: read current interface config before add/modify.
    # Only compare fields the user actually supplied — None fields are ignored.
    # If chpvc network show fails, current=None → helpers return False → proceeds.
    if component == 'network' and state in ('present', 'modify'):
        current_net = _read_network_current(module, host_ip, user, password, interface)
        if _network_already_matches(current_net, address, netmask, gateway):
            module.exit_json(
                changed=False, rc=0,
                stdout_lines=["Network interface already in desired state — no change required"],
                msg="Network interface already in desired state — no change required"
            )

    # update_dns idempotency: read /etc/hosts before add/remove.
    # modify is always mutating — no meaningful idempotency for value replacement.
    if component == 'update_dns' and state in ('present', 'absent') and entry:
        current_entries = _read_update_dns_current(module, host_ip, user, password)
        if state == 'present' and _update_dns_entry_exists(current_entries, entry):
            module.exit_json(
                changed=False, rc=0,
                stdout_lines=["Hosts entry already present — no change required"],
                msg="Hosts entry already present — no change required"
            )
        if state == 'absent' and not _update_dns_entry_exists(current_entries, entry):
            module.exit_json(
                changed=False, rc=0,
                stdout_lines=["Hosts entry already absent — no change required"],
                msg="Hosts entry already absent — no change required"
            )

    # DNS idempotency: read current state before deciding whether to act.
    # This also makes check_mode accurate — it reports the real desired-vs-actual
    # delta instead of always claiming changed=True.
    if component == 'dns' and state in ('present', 'absent'):
        cur_servers, cur_suffixes = _read_dns_current(module, host_ip, user, password)
        if state == 'present' and _dns_already_present(
                cur_servers, cur_suffixes, dns_server, domain_suffix):
            module.exit_json(
                changed=False, rc=0,
                stdout_lines=["DNS entry already present — no change required"],
                msg="DNS entry already present — no change required"
            )
        if state == 'absent' and _dns_already_absent(
                cur_servers, cur_suffixes, dns_server, domain_suffix):
            module.exit_json(
                changed=False, rc=0,
                stdout_lines=["DNS entry already absent — no change required"],
                msg="DNS entry already absent — no change required"
            )

    command, messages = construct_command(
        state, component, address, netmask, interface, gateway,
        position, route_type, dns_server, domain_suffix,
        action, ntp_servers, ntp_trust_servers, entry, new_entry)

    if command is None:
        err_msg = messages.get('error', 'Invalid component/state combination')
        module.fail_json(changed=False, msg=err_msg)

    # check_mode: show is read-only so changed=False; all others would mutate.
    # DNS check_mode lands here only when a real change is needed (idempotency
    # check above already exited for no-op cases).
    if module.check_mode:
        module.exit_json(
            changed=(state != 'show'),
            rc=0,
            stdout_lines=[],
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host_ip, user, password,
                            command=command, messages=messages)
    try:
        rc, output = connection.run()
    except (CLIError, Exception) as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        stderr_msg = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(
            changed=False,
            rc=int(rc),
            msg=f"Network management command failed with rc={rc}",
            stderr=stderr_msg
        )

    lines = output if isinstance(output, list) else ([str(output)] if output else [])

    # chpvc sometimes exits 0 but embeds an ERROR block in stdout.
    # Detect this and surface it as a proper failure so changed stays False.
    if _stdout_has_error(lines):
        module.fail_json(
            changed=False,
            rc=int(rc),
            msg="Network management command reported an error in output",
            stderr="\n".join(lines)
        )

    # state=show is read-only for all components — never modifies configuration
    # For ntp: enable/disable/set/unset/restart all mutate state
    module.exit_json(
        changed=(state != 'show'),
        rc=int(rc),
        stdout_lines=lines,
        msg="Network management completed successfully"
    )


def main():
    '''Main execution'''
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            component=dict(type='str', required=True,
                           choices=['firewall', 'route', 'network', 'dns', 'ntp',
                                    'update_dns']),
            state=dict(type='str', required=True,
                       choices=['present', 'absent', 'modify', 'show']),
            action=dict(type='str', required=False,
                        choices=['set', 'unset', 'restart']),
            address=dict(type='str', required=False),
            netmask=dict(type='str', required=False),
            interface=dict(type='str', required=False),
            gateway=dict(type='str', required=False),
            position=dict(type='str', required=False),
            route_type=dict(type='str', required=False, choices=['host', 'net']),
            dns_server=dict(type='str', required=False),
            domain_suffix=dict(type='str', required=False),
            ntp_servers=dict(type='str', required=False),
            ntp_trust_servers=dict(type='str', required=False),
            entry=dict(type='str', required=False),
            new_entry=dict(type='str', required=False),
        ),
        supports_check_mode=True
    )

    run_network_management(module)


if __name__ == '__main__':
    main()
