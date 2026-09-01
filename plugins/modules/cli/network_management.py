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
  - C(component=dns) supports C(state=present) (C(chpvc network_dns add)) and
    C(state=absent) (C(chpvc network_dns remove)) only; C(state=show) is not
    supported by the CLI.
  - C(component=dns) is idempotent — C(state=present) reads C(/etc/resolv.conf) via SSH
    and skips the command if the DNS server and/or domain suffix are already configured.
    C(state=absent) skips the command if the entries are already absent.
    C(--check) mode also reads C(/etc/resolv.conf) so it correctly reports
    C(changed=false) when the system is already compliant.
  - C(component=ntp), C(state=show) maps to C(chpvc ntp status) and is read-only.
  - C(component=ntp), C(state=present) maps to C(chpvc ntp enable); idempotent —
    reads C(chpvc ntp status) first and skips if chronyd is already enabled.
  - C(component=ntp), C(state=absent) maps to C(chpvc ntp disable); idempotent —
    reads C(chpvc ntp status) first and skips if chronyd is already disabled.
  - C(component=ntp), C(action=set) sets NTP servers via C(chpvc ntp set); idempotent —
    reads C(/etc/chrony.conf) and skips if all requested servers are already configured.
  - C(component=ntp), C(action=unset) removes NTP servers via C(chpvc ntp unset);
    idempotent — reads C(/etc/chrony.conf) and skips if none of the requested servers
    are currently present in the configuration.
  - C(component=ntp), C(action=restart) restarts chronyd via C(chpvc ntp restart);
    always mutates (restart is not idempotent by nature).
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
      - C(set) — set NTP servers (requires C(ntp_servers) or C(ntp_trust_servers));
        optionally adds iburst to plain servers via C(ntp_iburst).
      - C(unset) — remove NTP servers (requires C(ntp_servers)); optionally removes
        the iburst flag from servers via C(ntp_iburst).
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
  ntp_iburst:
    description:
      - Comma-separated list of NTP server addresses for which to apply the
        iburst flag.
      - Used with C(action=set) (maps to C(--iburst)) to add iburst to plain
        servers (trust-servers receive iburst automatically).
      - Used with C(action=unset) (maps to C(--iburst)) to remove the iburst
        flag from servers without removing the server entry itself.
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
        ntp_iburst: "{{ ntp_iburst }}"
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
        ntp_iburst: "{{ ntp_iburst }}"
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
    C(false) for C(state=show) (read-only), on failure, or when the system is
    already in the desired state (idempotent pre-read guard fired).
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
                          ntp_trust_servers=None, ntp_iburst=None):
    '''Construct the chpvc ntp command.

    Mapping:
      state=show                      → chpvc ntp status
      state=present  (no action)      → chpvc ntp enable
      state=absent   (no action)      → chpvc ntp disable
      state=present, action=set       → chpvc ntp set [--servers ...] [--trust-servers ...] [--iburst ...]
      state=absent,  action=unset     → chpvc ntp unset [--servers ...] [--iburst ...]
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
        if ntp_iburst is not None:
            command += f" --iburst {ntp_iburst}"
        return command

    if action == 'unset':
        command = "chpvc ntp unset"
        if ntp_servers is not None:
            command += f" --servers {ntp_servers}"
        if ntp_iburst is not None:
            command += f" --iburst {ntp_iburst}"
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


# Matches ANSI escape sequences so they can be stripped before parsing.
import re as _re
_ANSI_ESCAPE = _re.compile(r'\x1b(?:\[[0-9;]*[A-Za-z]|\][^\x07\x1b]*[\x07\x1b]|c)')


def _strip_ansi_nm(s):
    return _ANSI_ESCAPE.sub('', s)


def _parse_ntp_status(lines):
    '''Parse output of ``chpvc ntp status`` into a dict with keys:

      ``enabled``  (bool)   — True when any line contains the word "enabled"
                              (after ANSI stripping).  False when "disabled"
                              is found first.  chpvc ntp output does not use
                              a key:value format — it emits plain messages such
                              as "chronyd enabled" or "chronyd disabled" inside
                              a decorative box.
      ``servers``  (set)    — normalised (stripped, lowercased) server addresses
                              extracted from any "NTP Servers" / "Servers" line
                              that uses the key : value format.

    Returns a dict with at least ``enabled`` set when the output is parseable.
    Callers treat an empty dict as "unknown — skip idempotency".
    '''
    result = {}
    for raw_line in lines:
        line = _strip_ansi_nm(raw_line).strip().lower()
        if not line:
            continue

        # Plain-text enable/disable detection — no colon required.
        # Matches "chronyd enabled", "ntp enabled", "service: enabled", etc.
        if 'enabled' in line and 'disabled' not in line:
            result['enabled'] = True
        elif 'disabled' in line:
            result['enabled'] = False

        # Server list — only present in key : value lines.
        if ':' in line and 'server' in line:
            _, _, val = line.partition(':')
            val = val.strip()
            if val:
                result['servers'] = {
                    s.strip() for s in val.split(',') if s.strip()
                }
    return result


def _read_ntp_status(module, host_ip, user, password):
    '''Read current NTP status via ``chpvc ntp status``.

    Returns the dict from ``_parse_ntp_status``, or an empty dict on any
    failure — callers treat an empty dict as "skip idempotency".
    '''
    connection = Connection(module, host_ip, user, password,
                            command="chpvc ntp status", messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return {}

    if int(rc) != 0:
        return {}

    lines = output if isinstance(output, list) else str(output).splitlines()
    return _parse_ntp_status(lines)


def _read_chrony_conf(module, host_ip, user, password):
    '''Read configured NTP servers from ``/etc/chrony.conf`` via SSH.

    Returns a set of lowercased server/pool addresses currently in the file.
    Returns None on any failure so callers skip idempotency rather than aborting.

    Relevant /etc/chrony.conf directives:
        server   10.0.0.1 iburst
        pool     time.google.com iburst
        peer     10.0.0.2
    The first token after the directive keyword is the address.
    '''
    connection = Connection(module, host_ip, user, password,
                            command="cat /etc/chrony.conf", messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None

    if int(rc) != 0:
        return None

    lines = output if isinstance(output, list) else str(output).splitlines()
    servers = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if len(parts) >= 2 and parts[0].lower() in ('server', 'pool', 'peer'):
            servers.add(parts[1].strip().lower())
    return servers


def _read_resolv_conf(module, host_ip, user, password):
    '''Read current DNS configuration from ``/etc/resolv.conf`` via SSH.

    Returns a dict with:
      ``nameservers``  (set)  — lowercased IP addresses from ``nameserver`` lines
      ``search``       (set)  — lowercased domain names from ``search``/``domain`` lines

    Returns None on any failure so callers skip idempotency rather than aborting.

    /etc/resolv.conf format (relevant lines):
        nameserver 10.0.0.1
        nameserver 10.0.0.2
        search example.com local.domain
        domain example.com
    '''
    connection = Connection(module, host_ip, user, password,
                            command="cat /etc/resolv.conf", messages={})
    try:
        rc, output = connection.run()
    except Exception:
        return None

    if int(rc) != 0:
        return None

    lines = output if isinstance(output, list) else str(output).splitlines()
    nameservers = set()
    search_domains = set()
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        parts = line.split()
        if not parts:
            continue
        directive = parts[0].lower()
        if directive == 'nameserver' and len(parts) >= 2:
            nameservers.add(parts[1].strip().lower())
        elif directive in ('search', 'domain') and len(parts) >= 2:
            for domain in parts[1:]:
                search_domains.add(domain.strip().lower())
    return {'nameservers': nameservers, 'search': search_domains}


def construct_dns_command(state, dns_server=None, domain_suffix=None):
    '''Construct the chpvc network_dns command.

    Only add (state=present) and remove (state=absent) are supported by the CLI.
    state=show is not available for network_dns.
    '''
    if state == 'present':
        command = "chpvc network_dns add"
    elif state == 'absent':
        command = "chpvc network_dns remove"
    else:
        return None
    if dns_server is not None:
        command += f" --dns-server {dns_server}"
    if domain_suffix is not None:
        command += f" --domain-suffix {domain_suffix}"
    return command



# Interactive confirmation prompt emitted by `chpvc network modify`.
_NETWORK_MODIFY_PROMPT = r"Do you want to proceed\? \(yes/no\):"


def construct_command(state, component, address=None, netmask=None,
                      interface=None, gateway=None, position=None,
                      route_type=None, dns_server=None, domain_suffix=None,
                      action=None, ntp_servers=None, ntp_trust_servers=None,
                      ntp_iburst=None, entry=None, new_entry=None):
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
        command = construct_ntp_command(state, action, ntp_servers, ntp_trust_servers,
                                        ntp_iburst)
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
    ntp_iburst = module.params.get('ntp_iburst')
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

    # dns idempotency: read /etc/resolv.conf before add/remove.
    # chpvc network_dns has no show subcommand, so we cat /etc/resolv.conf directly.
    # If the read fails, current=None → skip idempotency check and proceed.
    #   present → skip if dns_server already in nameservers, or domain_suffix already in search
    #   absent  → skip if dns_server not in nameservers, or domain_suffix not in search
    if component == 'dns' and state in ('present', 'absent'):
        current_dns = _read_resolv_conf(module, host_ip, user, password)
        if current_dns is not None:
            if state == 'present':
                server_present = (
                    dns_server is not None and
                    dns_server.strip().lower() in current_dns['nameservers']
                )
                suffix_present = (
                    domain_suffix is not None and
                    domain_suffix.strip().lower() in current_dns['search']
                )
                # Only skip when every supplied field is already present
                supplied_server = dns_server is not None
                supplied_suffix = domain_suffix is not None
                if ((not supplied_server or server_present) and
                        (not supplied_suffix or suffix_present)):
                    module.exit_json(
                        changed=False, rc=0,
                        stdout_lines=["DNS configuration already present — no change required"],
                        msg="DNS configuration already present — no change required"
                    )
            elif state == 'absent':
                server_absent = (
                    dns_server is None or
                    dns_server.strip().lower() not in current_dns['nameservers']
                )
                suffix_absent = (
                    domain_suffix is None or
                    domain_suffix.strip().lower() not in current_dns['search']
                )
                if server_absent and suffix_absent:
                    module.exit_json(
                        changed=False, rc=0,
                        stdout_lines=["DNS configuration already absent — no change required"],
                        msg="DNS configuration already absent — no change required"
                    )

    # ntp idempotency: read chpvc ntp status before any mutating operation.
    # If the read fails (empty dict) we skip the check and proceed — never abort.
    #   enable  → skip if chronyd is already enabled
    #   disable → skip if chronyd is already disabled
    #   set     → skip if every requested server is already in the current server list
    #   unset   → skip if none of the requested servers appear in the current list
    #   restart → always mutates; no meaningful idempotency
    if component == 'ntp' and state != 'show' and action != 'restart':
        ntp_current = _read_ntp_status(module, host_ip, user, password)

        if action is None and ntp_current:
            # enable / disable
            if state == 'present' and ntp_current.get('enabled') is True:
                module.exit_json(
                    changed=False, rc=0,
                    stdout_lines=["NTP (chronyd) is already enabled — no change required"],
                    msg="NTP (chronyd) is already enabled — no change required"
                )
            if state == 'absent' and ntp_current.get('enabled') is False:
                module.exit_json(
                    changed=False, rc=0,
                    stdout_lines=["NTP (chronyd) is already disabled — no change required"],
                    msg="NTP (chronyd) is already disabled — no change required"
                )

        if action == 'set':
            # chpvc ntp status does not expose the server list — read /etc/chrony.conf.
            current_servers = _read_chrony_conf(module, host_ip, user, password)
            if current_servers is not None:
                requested = {
                    s.strip().lower()
                    for src in (ntp_servers, ntp_trust_servers, ntp_iburst)
                    if src
                    for s in src.split(',')
                    if s.strip()
                }
                if requested and requested.issubset(current_servers):
                    module.exit_json(
                        changed=False, rc=0,
                        stdout_lines=["All requested NTP servers already configured — no change required"],
                        msg="All requested NTP servers already configured — no change required"
                    )

        if action == 'unset':
            # chpvc ntp status does not expose the server list — read /etc/chrony.conf.
            # Only check ntp_servers here — ntp_iburst removes a flag from an existing
            # server entry, not the server itself, so its presence in chrony.conf does
            # not indicate a no-op for the iburst removal.
            current_servers = _read_chrony_conf(module, host_ip, user, password)
            if current_servers is not None and ntp_servers:
                requested = {
                    s.strip().lower()
                    for s in ntp_servers.split(',')
                    if s.strip()
                }
                if requested and not requested.intersection(current_servers):
                    module.exit_json(
                        changed=False, rc=0,
                        stdout_lines=["None of the requested NTP servers are configured — no change required"],
                        msg="None of the requested NTP servers are configured — no change required"
                    )

    command, messages = construct_command(
        state, component, address, netmask, interface, gateway,
        position, route_type, dns_server, domain_suffix,
        action, ntp_servers, ntp_trust_servers, ntp_iburst, entry, new_entry)

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

    # state=show is read-only for all components — never modifies configuration.
    # component=dns: the CLI itself reports "No changes made" when add/remove is
    # a no-op (entry already present / already absent), so we detect that phrase
    # to return changed=False without needing a separate show command.
    # For ntp: enable/disable/set/unset/restart all mutate state.
    if component == 'dns' and state in ('present', 'absent'):
        joined = "\n".join(lines).lower()
        dns_changed = "no changes made" not in joined
    else:
        dns_changed = None

    changed = (state != 'show') if dns_changed is None else dns_changed
    module.exit_json(
        changed=changed,
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
            ntp_iburst=dict(type='str', required=False),
            entry=dict(type='str', required=False),
            new_entry=dict(type='str', required=False),
        ),
        supports_check_mode=True
    )

    run_network_management(module)


if __name__ == '__main__':
    main()
