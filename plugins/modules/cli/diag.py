#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: diag
author:
    - Fredolin Brone (@Fredolin-B-Brone1)
short_description: Collect diagnostic data from a PowerVC or PVCVA appliance
description:
  - This module triggers diagnostic data collection on a PowerVC Controller or
    PVCVA appliance using C(powervc-diag) and optionally copies the resulting
    bundle to a local path on the Ansible controller.
  - Three actions are supported: C(collect) triggers the collection and generates
    the bundle, C(fetch) copies an already-generated bundle to the Ansible
    controller, and C(collect_and_fetch) performs both in sequence.
  - When I(fetch_dest) is set and the action includes a fetch step, the module
    uses Paramiko SFTP to pull the bundle from the appliance to the Ansible
    controller — the password is never placed on the command line.
  - All shell arguments that flow into remote commands are quoted with
    C(shlex.quote) to prevent injection from paths that contain spaces or
    special characters.
  - The C(--noprompt) flag is always passed so the command runs non-interactively.
    Interactive password prompts (e.g. for HMC) are handled via I(hmc_password).
notes:
  - Diagnostic collection can take several minutes depending on environment size.
    Use I(maxwait) to extend per-command timeouts in large or high-scale
    environments (C(powervc-diag) default is 120 s; maximum useful value is 300 s).
  - The module uses a 3600-second (1 hour) SSH channel timeout — the same budget
    used by other long-running commands in this collection (e.g. C(backup)).
  - The supported PVCVA diagnostic command can be overridden via I(diag_command)
    if different from the default C(powervc-diag).
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
  action:
    description:
      - C(collect) — run C(powervc-diag) on the appliance and report the bundle path.
      - C(fetch) — copy an existing bundle from I(bundle_path) on the appliance
        to I(fetch_dest) on the Ansible controller. Requires I(bundle_path)
        and I(fetch_dest).
      - C(collect_and_fetch) — run collection then immediately fetch the
        bundle. Requires I(fetch_dest).
    required: false
    default: collect
    type: str
    choices: ['collect', 'fetch', 'collect_and_fetch']
  diag_command:
    description:
      - Override the default C(powervc-diag) command.
      - Use this to specify the confirmed PVCVA diagnostic command once available.
    required: false
    type: str
    default: powervc-diag
  os_user:
    description:
      - PowerVC user for authentication inside the diagnostic collection
        (maps to C(-u / --user)).
      - When omitted, C(powervc-diag) reads C(OS_USERNAME) from the environment
        or falls back to C(whoami).
    required: false
    type: str
  os_project:
    description:
      - PowerVC project scope for diagnostic authentication
        (maps to C(-r / --project)).
      - Defaults to C(ibm-default) when not specified.
    required: false
    type: str
  output_dir:
    description:
      - Directory on the appliance where the diagnostic bundle is written
        (maps to C(-o / --output-dir)).
      - Defaults to C(/powervchome/diagnostics) when not specified.
    required: false
    type: str
  archive_fname:
    description:
      - Base name (without extension) for the generated archive file
        (maps to C(-f / --archive-fname)).
      - C(powervc-diag) appends C(.tgz) automatically.
        Example: C(PowerVC-TS123456789) produces C(PowerVC-TS123456789.tgz).
    required: false
    type: str
  verbose:
    description:
      - Increase verbosity of diagnostic collection (maps to C(-v / --verbose)).
    required: false
    type: bool
    default: false
  management_node_only:
    description:
      - Collect log data from the management node only; skip all HMC and
        Novalink nodes (maps to C(-m / --management-node-only)).
    required: false
    type: bool
    default: false
  current_node_only:
    description:
      - (Deprecated in powervc-diag) Retrieve diagnostic information for node
        where command is executed (maps to C(-cur / --current-node-only)).
    required: false
    type: bool
    default: false
  maxwait:
    description:
      - Number of seconds to wait for each individual diagnostic sub-command
        (maps to C(-w / --maxwait)).
      - Default inside C(powervc-diag) is 120 s. Raise to up to 300 s for
        large or high-scale environments.
    required: false
    type: int
  addfile:
    description:
      - Additional file or list of files on the appliance that should be included
        in the bundle (maps to C(-a / --addfile)).
    required: false
    type: raw
  services:
    description:
      - List or comma-separated string of services/components to collect diagnostics for
        (maps to C(-s / --services)).
      - Valid values are C(nova), C(cinder), C(glance), C(neutron), C(keystone),
        C(bumblebee), C(ceilometer), C(panko), C(placement), C(gnocchi),
        C(ttv-validation), C(swift), C(powervc-ui-server), C(pacemaker),
        C(blazar), C(squall).
      - When omitted all services are collected.
    required: false
    type: raw
  hmc_list:
    description:
      - Comma-separated list of HMC hostnames, IP addresses, or display names
        for which to collect HMC diagnostics (maps to C(-c / --hmcinfo)).
      - Use C(all) to collect data from all registered HMCs.
    required: false
    type: str
    aliases: ['hmcinfo']
  hmc_password:
    description:
      - Password for the C(hscpe) account on the HMC(s)
        (maps to C(--hmc-password)).
      - When set, the interactive HMC password prompt is skipped.
    required: false
    type: str
    no_log: true
  novalink_list:
    description:
      - Comma-separated list of Novalink hostnames or IP addresses
        (maps to C(-l / --novalinkinfo)).
      - Use C(all) to collect from all registered Novalink hosts.
    required: false
    type: str
    aliases: ['novalinkinfo']
  imagenode_list:
    description:
      - Comma-separated list of image node hostnames or IP addresses
        (maps to C(-i / --imagenodeinfo)).
      - Use C(all) to collect from all registered image nodes.
      - When omitted, data is collected from all registered image nodes by default.
    required: false
    type: str
    aliases: ['imagenodeinfo']
  nfs_server:
    description:
      - NFS server address to which C(powervc-diag) should transfer the archive
        directly (maps to C(--nfs-server)).
      - Requires I(nfs_path).
    required: false
    type: str
  nfs_path:
    description:
      - Exported path on the NFS server, e.g. C(/exports/diag)
        (maps to C(--nfs-path)).
      - Required when I(nfs_server) is set.
    required: false
    type: str
  bundle_path:
    description:
      - Absolute path of an existing diagnostic bundle on the appliance.
      - Required when I(action=fetch).
      - Ignored when I(action=collect_and_fetch); the path is taken from the
        command output automatically.
    required: false
    type: str
  fetch_dest:
    description:
      - Local directory or file path on the Ansible controller where the bundle
        should be saved.
      - Required when I(action) is C(fetch) or C(collect_and_fetch).
    required: false
    type: str
    aliases: ['dest']
  login_port:
    description:
      - SSH port on the appliance.
    required: false
    type: int
    default: 22
'''

EXAMPLES = '''
# -- Collect all diagnostics (defaults) ------------------------------------
- name: Collect PowerVC diagnostics
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Trigger diagnostic collection
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect
      register: result

    - name: Show bundle path
      debug:
        var: result.bundle_path

# -- Collect with custom archive name and output directory ------------------
- name: Collect diagnostics with custom name
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect with archive name
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect
        output_dir: "{{ diag_output_dir }}"
        archive_fname: "{{ diag_archive_fname }}"
      register: result

    - name: Show result
      debug:
        var: result

# -- Collect specific services only -----------------------------------------
- name: Collect nova and cinder diagnostics
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect targeted service diagnostics
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect
        services:
          - nova
          - cinder
      register: result

    - name: Show result
      debug:
        var: result

# -- Management node only (skip HMC and Novalink) ---------------------------
- name: Collect management-node-only diagnostics
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect management node diagnostics
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect_and_fetch
        management_node_only: true
        fetch_dest: "{{ diag_fetch_dest }}"
      register: result

    - name: Show local bundle path
      debug:
        var: result.local_path

# -- Collect with HMC diagnostics -------------------------------------------
- name: Collect diagnostics including HMC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect with HMC data
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect_and_fetch
        hmc_list: "{{ diag_hmc_list }}"
        hmc_password: "{{ diag_hmc_password }}"
        fetch_dest: "{{ diag_fetch_dest }}"
      register: result

    - name: Show result
      debug:
        var: result

# -- Collect and fetch bundle to the Ansible controller ---------------------
- name: Collect diagnostics and retrieve bundle
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect and fetch diagnostic bundle
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect_and_fetch
        fetch_dest: "{{ diag_fetch_dest }}"
      register: result

    - name: Show where bundle was saved locally
      debug:
        var: result.local_path

    - name: Show bytes transferred
      debug:
        var: result.bytes_transferred

# -- Fetch an already-collected bundle --------------------------------------
- name: Fetch existing diagnostic bundle
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Copy bundle from appliance to Ansible controller
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: fetch
        bundle_path: "{{ diag_bundle_path }}"
        fetch_dest: "{{ diag_fetch_dest }}"
      register: result

    - name: Show local path
      debug:
        var: result.local_path

# -- Transfer directly to NFS (no local fetch needed) ----------------------
- name: Collect diagnostics and push to NFS
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Collect and send to NFS
      ibm.powervc.cli.diag:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        action: collect
        nfs_server: "{{ diag_nfs_server }}"
        nfs_path: "{{ diag_nfs_path }}"
      register: result

    - name: Show result
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether a diagnostic collection or fetch operation took place.
  returned: always
  type: bool
bundle_path:
  description: >
    Absolute path of the diagnostic bundle on the appliance.
    Present when action is C(collect) or C(collect_and_fetch) and the command
    reports a path in its output. Empty string when the path cannot be parsed.
  returned: when action is collect or collect_and_fetch
  type: str
local_path:
  description: >
    Local path on the Ansible controller where the bundle was saved.
    Present when action includes a fetch step.
  returned: when action is fetch or collect_and_fetch
  type: str
bytes_transferred:
  description: Number of bytes transferred during the fetch step.
  returned: when action includes a fetch step
  type: int
stdout_lines:
  description: Output lines from the diagnostic command.
  returned: when action includes collect
  type: list
  elements: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
rc:
  description: Return code from the diagnostic command.
  returned: when action includes collect
  type: int
command:
  description: Exact command string executed on the appliance.
  returned: when action includes collect
  type: str
'''

import os
import re
import shlex
import time
import paramiko

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule

# Default diagnostic command (confirmed for PowerVC).
_DEFAULT_DIAG_COMMAND = 'powervc-diag'

VALID_SERVICES = [
    'nova', 'cinder', 'glance', 'neutron', 'keystone', 'bumblebee',
    'ceilometer', 'panko', 'placement', 'gnocchi', 'ttv-validation',
    'swift', 'powervc-ui-server', 'pacemaker', 'blazar', 'squall'
]

# Regex patterns used to extract the bundle path from command output.
_BUNDLE_PATH_PATTERNS = [
    re.compile(r'(?:saved to|output|bundle|archive|file)[:\s]+(/\S+\.(?:tar\.gz|tgz|zip|tar))', re.IGNORECASE),
    re.compile(r'(?:saved to|output|bundle|archive|file)[:\s]+(powervc-diag_\S+\.tgz)', re.IGNORECASE),
    re.compile(r'(/powervchome/\S+\.(?:tar\.gz|tgz|zip|tar))'),
    re.compile(r'(/tmp/\S+\.(?:tar\.gz|tgz|zip|tar))'),
    re.compile(r'(/var/\S+\.(?:tar\.gz|tgz|zip|tar))'),
    re.compile(r'(/[^\s]+\.tgz)'),
    re.compile(r'\b(powervc-diag_\d+-\d+\.tgz)\b'),
]


def _format_services(services):
    '''
    Validate and format services list or comma-separated string.

    :param list|str services: Services input
    :return str|None: Formatted comma-separated string
    '''
    if not services:
        return None

    if isinstance(services, list):
        svc_list = [str(s).strip() for s in services if str(s).strip()]
    else:
        svc_list = [s.strip() for s in str(services).split(',') if s.strip()]

    invalid = [s for s in svc_list if s not in VALID_SERVICES]
    if invalid:
        raise ValueError(
            f"Invalid service(s): {', '.join(invalid)}. "
            f"Valid services are: {', '.join(VALID_SERVICES)}"
        )
    return ','.join(svc_list)


def _build_collect_command(params):
    '''
    Build the powervc-diag command string from module parameters.
    All user-supplied values are shell-quoted.
    --noprompt is always included so the command runs non-interactively.
    '''
    diag_command = params.get('diag_command') or _DEFAULT_DIAG_COMMAND
    parts = [shlex.quote(diag_command), '-n']

    if params.get('os_user'):
        parts += ['-u', shlex.quote(str(params['os_user']))]

    if params.get('os_project'):
        parts += ['-r', shlex.quote(str(params['os_project']))]

    if params.get('output_dir'):
        parts += ['-o', shlex.quote(str(params['output_dir']))]

    if params.get('archive_fname'):
        fname = str(params['archive_fname'])
        if fname.endswith('.tgz'):
            fname = fname[:-4]
        parts += ['-f', shlex.quote(fname)]

    if params.get('verbose'):
        parts.append('-v')

    if params.get('management_node_only'):
        parts.append('-m')

    if params.get('current_node_only'):
        parts.append('-cur')

    if params.get('maxwait') is not None:
        parts += ['-w', str(int(params['maxwait']))]

    if params.get('addfile'):
        addfile = params['addfile']
        if isinstance(addfile, list):
            for af in addfile:
                if str(af).strip():
                    parts += ['-a', shlex.quote(str(af).strip())]
        else:
            parts += ['-a', shlex.quote(str(addfile).strip())]

    if params.get('services'):
        svc_str = _format_services(params['services'])
        if svc_str:
            parts += ['-s', shlex.quote(svc_str)]

    if params.get('hmc_list'):
        parts += ['-c', shlex.quote(str(params['hmc_list']))]

    if params.get('hmc_password'):
        parts += ['--hmc-password', shlex.quote(str(params['hmc_password']))]

    if params.get('novalink_list'):
        parts += ['-l', shlex.quote(str(params['novalink_list']))]

    if params.get('imagenode_list'):
        parts += ['-i', shlex.quote(str(params['imagenode_list']))]

    if params.get('nfs_server'):
        parts += ['--nfs-server', shlex.quote(str(params['nfs_server']))]

    if params.get('nfs_path'):
        parts += ['--nfs-path', shlex.quote(str(params['nfs_path']))]

    return ' '.join(parts)


def _extract_bundle_path(output_lines, output_dir=None, archive_fname=None):
    '''
    Parse the bundle file path from powervc-diag stdout lines with fallback.
    '''
    out_dir = (output_dir or '/powervchome/diagnostics').rstrip('/')
    full_output = '\n'.join(output_lines) if isinstance(output_lines, list) else str(output_lines)
    for pattern in _BUNDLE_PATH_PATTERNS:
        match = pattern.search(full_output)
        if match:
            path = match.group(1).strip()
            # Exclude ansible-log sub-archive if full archive is available
            if '-ansible-log.tgz' in path and not (archive_fname and 'ansible-log' in str(archive_fname)):
                continue
            if not path.startswith('/'):
                path = f"{out_dir}/{path}"
            return re.sub(r'/+', '/', path)

    # Fallback to output_dir and archive_fname if provided
    if archive_fname:
        fname = str(archive_fname).strip()
        if not fname.endswith('.tgz'):
            fname = f"{fname}.tgz"
        return re.sub(r'/+', '/', f"{out_dir}/{fname}")

    return ''


def _open_ssh_transport(host_ip, port, user, password):
    '''
    Establish an authenticated Paramiko SSH Transport using keyboard-interactive
    or password authentication.
    '''
    sock_transport = paramiko.Transport((host_ip, port or 22))
    try:
        sock_transport.connect()

        def interactive_handler(title, instructions, prompts):
            responses = []
            for prompt, _echo in prompts:
                if "password" in prompt.lower():
                    responses.append(password)
                else:
                    responses.append("")
            return responses

        sock_transport.auth_interactive(user, interactive_handler)
        return sock_transport
    except Exception:
        try:
            sock_transport.connect(username=user, password=password)
            return sock_transport
        except Exception:
            sock_transport.close()
            raise


def _exec_ssh_cmd(transport, cmd, timeout=30):
    '''Execute a remote shell command over SSH transport and return stripped stdout.'''
    chan = transport.open_session()
    chan.settimeout(None)
    chan.exec_command(cmd)
    out_chunks = []
    deadline = time.monotonic() + timeout
    while True:
        if time.monotonic() > deadline:
            chan.close()
            raise IOError(f"Remote command timed out: {cmd}")
        drained = False
        while chan.recv_ready():
            out_chunks.append(chan.recv(4096).decode('utf-8', errors='replace'))
            drained = True
        if chan.exit_status_ready():
            break
        if not drained:
            time.sleep(0.05)
    while chan.recv_ready():
        out_chunks.append(chan.recv(4096).decode('utf-8', errors='replace'))
    chan.close()
    return ''.join(out_chunks).strip()


def _sftp_get_file(host_ip, port, user, password, remote_path, local_dest):
    '''
    Download a file from the appliance. Attempts Paramiko SFTP first, and if
    the SFTP subsystem is disabled on the appliance (EOF during negotiation),
    transparently falls back to streaming binary content over an SSH session channel.

    Returns (resolved_remote_path, local_path, bytes_transferred).
    '''
    transport = _open_ssh_transport(host_ip, port, user, password)
    try:
        # Normalize double slashes in remote_path if present
        if remote_path:
            remote_path = re.sub(r'/+', '/', remote_path.strip())

        # 1. Resolve remote path if empty or directory or wildcard
        if not remote_path or '*' in remote_path or not remote_path.endswith('.tgz'):
            find_dir = os.path.dirname(remote_path) if (remote_path and not os.path.isdir(remote_path)) else (remote_path or '/powervchome/diagnostics')
            find_dir = re.sub(r'/+', '/', find_dir.rstrip('/')) or '/powervchome/diagnostics'
            # Look for main diagnostic bundle (excluding ansible-log sub-archives), trying sudo if needed
            found = _exec_ssh_cmd(
                transport,
                f"sudo -n ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null || "
                f"sudo ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null || "
                f"ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null | grep -v 'ansible-log' | head -n 1"
            )
            if not found:
                found = _exec_ssh_cmd(
                    transport,
                    f"sudo -n ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null || "
                    f"sudo ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null || "
                    f"ls -1t {shlex.quote(find_dir)}/*.tgz 2>/dev/null | head -n 1"
                )
            if found:
                remote_path = re.sub(r'/+', '/', found.splitlines()[0].strip())
            else:
                raise IOError(f"No diagnostic archive (.tgz) found in {find_dir}")

        # Determine local target destination path
        if os.path.isdir(local_dest) or local_dest.endswith(('/', '\\')):
            os.makedirs(local_dest, exist_ok=True)
            target_filename = os.path.basename(remote_path)
            local_path = os.path.join(local_dest, target_filename)
        else:
            parent_dir = os.path.dirname(os.path.abspath(local_dest))
            if parent_dir:
                os.makedirs(parent_dir, exist_ok=True)
            local_path = local_dest

        # 2. Try SFTP if the SFTP subsystem daemon is enabled on remote sshd
        sftp = None
        try:
            sftp = paramiko.SFTPClient.from_transport(transport)
            remote_stat = sftp.stat(remote_path)
            sftp.get(remote_path, local_path)
            bytes_transferred = remote_stat.st_size or os.path.getsize(local_path)
            return remote_path, local_path, bytes_transferred
        except Exception:
            # SFTP unavailable -> Seamless fallback to SSH session channel streaming
            pass
        finally:
            if sftp is not None:
                try:
                    sftp.close()
                except Exception:
                    pass

        # 3. SSH Channel Streaming Fallback (works across all appliances without SFTP subsystem)
        chan = transport.open_session()
        chan.settimeout(None)
        # Use sudo fallback to ensure non-root users (e.g. pvcroot) can read root-owned (0600) diagnostic archives
        stream_cmd = (
            f"sudo -n cat {shlex.quote(remote_path)} 2>/dev/null || "
            f"sudo cat {shlex.quote(remote_path)} 2>/dev/null || "
            f"cat {shlex.quote(remote_path)}"
        )
        chan.exec_command(stream_cmd)
        bytes_transferred = 0
        err_chunks = []
        with open(local_path, 'wb') as f:
            deadline = time.monotonic() + 3600
            while True:
                if time.monotonic() > deadline:
                    chan.close()
                    raise IOError(f"File download timed out for {remote_path}")
                drained = False
                while chan.recv_ready():
                    chunk = chan.recv(65536)
                    if chunk:
                        f.write(chunk)
                        bytes_transferred += len(chunk)
                        drained = True
                if hasattr(chan, 'recv_stderr_ready'):
                    while chan.recv_stderr_ready():
                        err_chunk = chan.recv_stderr(4096)
                        if err_chunk:
                            err_chunks.append(err_chunk.decode('utf-8', errors='replace'))
                            drained = True
                if chan.exit_status_ready():
                    break
                if not drained:
                    time.sleep(0.02)
            # Drain any remaining bytes after exit status
            while chan.recv_ready():
                chunk = chan.recv(65536)
                if chunk:
                    f.write(chunk)
                    bytes_transferred += len(chunk)
            if hasattr(chan, 'recv_stderr_ready'):
                while chan.recv_stderr_ready():
                    err_chunk = chan.recv_stderr(4096)
                    if err_chunk:
                        err_chunks.append(err_chunk.decode('utf-8', errors='replace'))

        exit_status = chan.recv_exit_status()
        chan.close()

        if exit_status != 0:
            if os.path.exists(local_path):
                try:
                    os.remove(local_path)
                except OSError:
                    pass
            err_msg = ''.join(err_chunks).strip()
            detail = f": {err_msg}" if err_msg else ""
            raise IOError(f"Failed to read remote file {remote_path} via SSH (exit status {exit_status}){detail}")

        if bytes_transferred == 0:
            raise IOError(f"Diagnostic archive at {remote_path} is empty or unreadable")

        return remote_path, local_path, bytes_transferred

    finally:
        if transport is not None:
            try:
                transport.close()
            except Exception:
                pass


def run_collect(module):
    '''Trigger powervc-diag on the appliance. Returns result dict.'''
    p = module.params
    try:
        cmd = _build_collect_command(p)
    except ValueError as e:
        module.fail_json(msg=str(e), changed=False)

    conn = Connection(module, p['login_host'], p['login_user'],
                      p['login_password'], command=cmd)
    try:
        rc, output_lines = conn.run()
    except Exception as e:
        module.fail_json(msg=f"Diagnostic collection failed: {e}", command=cmd, changed=False)

    if int(rc) != 0:
        stderr_str = '\n'.join(output_lines) if isinstance(output_lines, list) else str(output_lines)
        module.fail_json(
            msg=f"powervc-diag exited with rc={rc}",
            rc=int(rc),
            command=cmd,
            stderr=stderr_str,
            stdout_lines=output_lines,
            changed=False
        )

    bundle_path = _extract_bundle_path(
        output_lines,
        output_dir=p.get('output_dir'),
        archive_fname=p.get('archive_fname')
    )

    return {
        'changed': True,
        'command': cmd,
        'bundle_path': bundle_path,
        'stdout_lines': output_lines,
        'msg': 'Diagnostic collection completed successfully',
        'rc': int(rc),
    }


def run_fetch(module, bundle_path_override=None):
    '''Fetch a diagnostic bundle from the appliance. Returns result dict.'''
    p = module.params
    bundle_path = bundle_path_override or p.get('bundle_path')
    fetch_dest = p.get('fetch_dest')

    if not bundle_path:
        module.fail_json(msg="bundle_path is required for action=fetch", changed=False)
    if not fetch_dest:
        module.fail_json(msg="fetch_dest is required for action=fetch or collect_and_fetch", changed=False)

    try:
        resolved_remote, local_path, bytes_transferred = _sftp_get_file(
            p['login_host'], p.get('login_port', 22),
            p['login_user'], p['login_password'],
            bundle_path, fetch_dest
        )
    except paramiko.AuthenticationException as e:
        module.fail_json(msg=f"SSH authentication failed during fetch: {e}", changed=False)
    except paramiko.SSHException as e:
        module.fail_json(msg=f"SSH error during fetch: {e}", changed=False)
    except IOError as e:
        module.fail_json(msg=f"File transfer error during fetch: {e}", changed=False)
    except Exception as e:
        module.fail_json(msg=f"Unexpected error during fetch: {e}", changed=False)

    return {
        'changed': True,
        'bundle_path': resolved_remote,
        'local_path': local_path,
        'bytes_transferred': bytes_transferred,
        'msg': f"Diagnostic bundle fetched to {local_path}",
    }


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            action=dict(
                type='str', required=False, default='collect',
                choices=['collect', 'fetch', 'collect_and_fetch']
            ),
            diag_command=dict(type='str', required=False, default='powervc-diag'),
            # powervc-diag authentication options
            os_user=dict(type='str', required=False),
            os_project=dict(type='str', required=False),
            # output / archive options
            output_dir=dict(type='str', required=False),
            archive_fname=dict(type='str', required=False),
            # behaviour flags
            verbose=dict(type='bool', required=False, default=False),
            management_node_only=dict(type='bool', required=False, default=False),
            current_node_only=dict(type='bool', required=False, default=False),
            maxwait=dict(type='int', required=False),
            addfile=dict(type='raw', required=False),
            # scope options
            services=dict(type='raw', required=False),
            hmc_list=dict(type='str', required=False, aliases=['hmcinfo']),
            hmc_password=dict(type='str', required=False, no_log=True),
            novalink_list=dict(type='str', required=False, aliases=['novalinkinfo']),
            imagenode_list=dict(type='str', required=False, aliases=['imagenodeinfo']),
            # NFS direct transfer
            nfs_server=dict(type='str', required=False),
            nfs_path=dict(type='str', required=False),
            # fetch-to-controller options
            bundle_path=dict(type='str', required=False),
            fetch_dest=dict(type='str', required=False, aliases=['dest']),
            login_port=dict(type='int', required=False, default=22),
        ),
        required_if=[
            ('action', 'fetch', ['bundle_path', 'fetch_dest']),
            ('action', 'collect_and_fetch', ['fetch_dest']),
        ],
        required_together=[
            ['nfs_server', 'nfs_path'],
        ],
        supports_check_mode=True
    )

    action = module.params['action']

    if module.check_mode:
        try:
            cmd = _build_collect_command(module.params) if action != 'fetch' else '(fetch only)'
        except Exception as e:
            module.fail_json(msg=str(e), changed=False)

        module.exit_json(
            changed=True,
            msg=f"[CHECK MODE] Would run action='{action}' on "
                f"{module.params['login_host']}: {cmd}"
        )

    if action == 'collect':
        result = run_collect(module)

    elif action == 'fetch':
        result = run_fetch(module)

    elif action == 'collect_and_fetch':
        collect_result = run_collect(module)
        bundle_path = collect_result.get('bundle_path')
        if not bundle_path:
            module.fail_json(
                msg=(
                    "collect_and_fetch: collection succeeded but the bundle path "
                    "could not be determined from the command output. "
                    "Use action=collect to inspect the output, then action=fetch "
                    "with an explicit bundle_path."
                ),
                stdout_lines=collect_result.get('stdout_lines', []),
                changed=True
            )
        fetch_result = run_fetch(module, bundle_path_override=bundle_path)
        result = {
            'changed': True,
            'command': collect_result.get('command'),
            'bundle_path': bundle_path,
            'local_path': fetch_result['local_path'],
            'bytes_transferred': fetch_result['bytes_transferred'],
            'stdout_lines': collect_result.get('stdout_lines', []),
            'rc': collect_result.get('rc', 0),
            'msg': f"Diagnostic bundle collected and fetched to {fetch_result['local_path']}",
        }

    else:
        module.fail_json(msg=f"Unsupported action: {action}")

    module.exit_json(**result)


if __name__ == '__main__':
    main()
