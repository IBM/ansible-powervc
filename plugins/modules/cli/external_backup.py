#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: external_backup
author:
    - Fredolin Brone
short_description: Copy a PowerVC backup to an external storage target
description:
  - This module copies an existing PowerVC local backup to an external storage
    target to ensure backup data is preserved outside the PowerVC appliance.
  - Supported targets are C(nfs) and C(cos) (IBM Cloud Object Storage).
  - For NFS, the remote filesystem is mounted only for the duration of the copy
    and immediately unmounted once the transfer is complete. This avoids a
    permanent NFS dependency on the PowerVC nodes.
  - A failed unmount is treated as a fatal error even when the backup copy
    succeeded, because a mounted NFS share left on a PowerVC node violates the
    core requirement of this feature.
  - All parameters that appear in shell commands are shell-quoted with
    C(shlex.quote) to prevent path injection from names that contain spaces or
    special characters.
  - The module connects to the PowerVC Controller over SSH (using the same
    Paramiko transport as other modules in this collection) and runs all
    mount/copy/unmount operations remotely on the controller itself.
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
  backup_dir:
    description:
      - Path on the PowerVC Controller that contains the local backup files.
        Defaults to C(/powervchome/backups).
    required: false
    type: str
    default: /powervchome/backups
  target_type:
    description:
      - External storage target type.
      - C(nfs) — mount an NFS share, copy the backup, then unmount.
      - C(cos) — upload the backup to IBM Cloud Object Storage using the
        C(aws s3 cp) CLI (compatible with the IBM COS S3 API).
    required: true
    type: str
    choices: ['nfs', 'cos']
  nfs_server:
    description:
      - NFS server hostname or IP address.
      - Required when C(target_type=nfs).
    required: false
    type: str
  nfs_export:
    description:
      - Exported NFS path on the server (e.g. C(/exports/powervc-backups)).
      - Required when C(target_type=nfs).
    required: false
    type: str
  nfs_mount_point:
    description:
      - Temporary local directory on the PowerVC Controller to use as the NFS
        mount point. Created automatically if it does not exist.
      - The directory is unmounted immediately after the copy. It is not
        deleted; the mount point is left in place for reuse on future runs.
      - Defaults to C(/mnt/powervc_external_backup).
    required: false
    type: str
    default: /mnt/powervc_external_backup
  nfs_options:
    description:
      - Extra mount options forwarded to the C(mount -o) flag (e.g.
        C(rw,sync,soft,timeo=30)). Passed verbatim; leave empty to use
        system defaults.
    required: false
    type: str
    default: ''
  cos_endpoint:
    description:
      - IBM COS S3-compatible endpoint URL
        (e.g. C(https://s3.us-south.cloud-object-storage.appdomain.cloud)).
      - Required when C(target_type=cos).
    required: false
    type: str
  cos_bucket:
    description:
      - Target COS bucket name.
      - Required when C(target_type=cos).
    required: false
    type: str
  cos_access_key:
    description:
      - HMAC access key ID for the COS bucket.
      - Required when C(target_type=cos).
    required: false
    type: str
    no_log: true
  cos_secret_key:
    description:
      - HMAC secret access key for the COS bucket.
      - Required when C(target_type=cos).
    required: false
    type: str
    no_log: true
  cos_prefix:
    description:
      - Optional key prefix (folder path) inside the COS bucket where the
        backup files are stored (e.g. C(powervc/backups/)).
      - A trailing slash is appended automatically if missing.
    required: false
    type: str
    default: ''
'''

EXAMPLES = '''
- name: "External backup to NFS"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Copy latest backup to NFS share"
      ibm.powervc.cli.external_backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        backup_dir: "/powervchome/backups"
        target_type: "nfs"
        nfs_server: "{{ ext_backup_nfs_server }}"
        nfs_export: "{{ ext_backup_nfs_export }}"
        nfs_mount_point: "{{ ext_backup_nfs_mount_point }}"
        nfs_options: "{{ ext_backup_nfs_options }}"
      register: result

    - name: "Show result"
      debug:
        var: result


- name: "External backup to IBM Cloud Object Storage"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Upload latest backup to COS bucket"
      ibm.powervc.cli.external_backup:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        backup_dir: "/powervchome/backups"
        target_type: "cos"
        cos_endpoint: "{{ ext_backup_cos_endpoint }}"
        cos_bucket: "{{ ext_backup_cos_bucket }}"
        cos_access_key: "{{ ext_backup_cos_access_key }}"
        cos_secret_key: "{{ ext_backup_cos_secret_key }}"
        cos_prefix: "{{ ext_backup_cos_prefix }}"
      register: result

    - name: "Show result"
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the external backup copy was carried out.
  returned: always
  type: bool
target_type:
  description: The external target type that was used (C(nfs) or C(cos)).
  returned: always
  type: str
backup_dir:
  description: The parent directory that was searched for backups.
  returned: always
  type: str
latest_backup:
  description: Absolute path of the most-recently-modified entry inside
    C(backup_dir) that was selected and copied to the external target.
  returned: success
  type: str
msg:
  description: Human-readable status message.
  returned: always
  type: str
stdout_lines:
  description: Combined output of the remote commands (mount, copy, unmount).
  returned: success
  type: list
  elements: str
'''

import shlex

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible.module_utils.basic import AnsibleModule


# ---------------------------------------------------------------------------
# Command builders
# ---------------------------------------------------------------------------

def _build_latest_cmd(backup_dir):
    """
    Return a shell command that prints the absolute path of the
    most-recently-modified entry (file or directory) directly inside
    ``backup_dir``, with no trailing newline noise.

    ``ls -1td`` lists immediate children sorted by modification time,
    newest first.  ``head -1`` keeps only the first line.  The result is
    the path of the latest backup entry.

    ``backup_dir`` is shell-quoted to handle paths with spaces or special
    characters.
    """
    return f"ls -1td {shlex.quote(backup_dir)}/* | head -1"


def _build_nfs_commands(latest_path, nfs_server, nfs_export,
                        mount_point, nfs_options):
    """
    Return the ordered list of shell commands for the NFS workflow:
      1. mkdir -p  <mount_point>
      2. mount [-o <options>] <server>:<export> <mount_point>
      3. cp -rp    <latest_path> <mount_point>/
      4. umount    <mount_point>

    The mount-point directory is created if absent but intentionally left in
    place after unmounting.  Deleting it is not part of the requirement and
    would fail when the directory is still in use or when the operator
    chooses to reuse the same path across runs.

    ``latest_path`` is the resolved absolute path of the single backup entry
    to copy (produced by ``_build_latest_cmd``).

    All variable components are shell-quoted with ``shlex.quote``.  Note that
    ``nfs_options`` is a comma-separated option string passed directly to
    ``mount -o``; it is quoted as a single token so its value is treated
    literally by the shell.
    """
    q_mp = shlex.quote(mount_point)
    q_latest = shlex.quote(latest_path)
    q_server = shlex.quote(nfs_server)
    q_export = shlex.quote(nfs_export)

    mkdir_cmd = f"mkdir -p {q_mp}"

    if nfs_options:
        mount_cmd = (
            f"mount -t nfs -o {shlex.quote(nfs_options)} "
            f"{q_server}:{q_export} {q_mp}"
        )
    else:
        mount_cmd = f"mount -t nfs {q_server}:{q_export} {q_mp}"

    copy_cmd = f"cp -rp {q_latest} {q_mp}/"
    umount_cmd = f"umount {q_mp}"

    return [mkdir_cmd, mount_cmd, copy_cmd, umount_cmd]


def _build_cos_command(latest_path, cos_endpoint, cos_bucket,
                       cos_access_key, cos_secret_key, cos_prefix):
    """
    Return a single aws-cli s3-compatible command that uploads the latest
    backup entry recursively to the COS bucket.

    ``latest_path`` is the resolved absolute path of the single backup entry
    to upload (produced by ``_build_latest_cmd``).

    Credentials are injected via environment variables (AWS_ACCESS_KEY_ID and
    AWS_SECRET_ACCESS_KEY) prepended to the command so that they are never
    stored in shell history or visible in process listings beyond the
    duration of the command.  The credential *values* are shell-quoted so that
    keys containing special characters are passed safely.

    The trailing ``/`` on the destination URL ensures objects are placed
    inside the prefix "folder", not at bucket root.

    All variable components are shell-quoted with ``shlex.quote``.
    """
    # Normalise prefix: ensure trailing slash when non-empty
    prefix = cos_prefix
    if prefix and not prefix.endswith('/'):
        prefix += '/'

    dest = f"s3://{cos_bucket}/{prefix}"

    cmd = (
        f"AWS_ACCESS_KEY_ID={shlex.quote(cos_access_key)} "
        f"AWS_SECRET_ACCESS_KEY={shlex.quote(cos_secret_key)} "
        f"aws s3 cp {shlex.quote(latest_path)} {shlex.quote(dest)} "
        f"--recursive "
        f"--endpoint-url {shlex.quote(cos_endpoint)}"
    )
    return cmd


# ---------------------------------------------------------------------------
# Validation helpers
# ---------------------------------------------------------------------------

def _validate_nfs_params(module):
    """Fail with a descriptive message when required NFS params are missing."""
    missing = []
    for param in ('nfs_server', 'nfs_export'):
        if not module.params.get(param):
            missing.append(param)
    if missing:
        module.fail_json(
            changed=False,
            msg=f"target_type=nfs requires: {', '.join(missing)}"
        )


def _validate_cos_params(module):
    """Fail with a descriptive message when required COS params are missing."""
    missing = []
    for param in ('cos_endpoint', 'cos_bucket', 'cos_access_key', 'cos_secret_key'):
        if not module.params.get(param):
            missing.append(param)
    if missing:
        module.fail_json(
            changed=False,
            msg=f"target_type=cos requires: {', '.join(missing)}"
        )


# ---------------------------------------------------------------------------
# Execution helpers
# ---------------------------------------------------------------------------

def _run_command(module, connection, cmd, context):
    """
    Execute *cmd* on the controller and fail loudly on non-zero exit.

    :param module:       AnsibleModule instance
    :param connection:   Connection instance (already authenticated)
    :param str cmd:      Shell command to execute
    :param str context:  Human-readable label for error messages
    :return list[str]:   Output lines
    """
    connection.cmd = cmd
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=f"{context} failed: {e}")

    if int(rc) != 0:
        stderr_str = "\n".join(output) if isinstance(output, list) else str(output)
        module.fail_json(
            changed=False,
            msg=f"{context} failed (rc={rc})",
            rc=int(rc),
            stderr=stderr_str
        )
    return output if output else []


def _run_command_tolerant(connection, cmd):
    """
    Execute *cmd* without raising or calling fail_json on failure.

    Used for cleanup steps (umount, rmdir) that must always run even when a
    preceding step failed.  Returns ``(rc, output_lines)``.
    """
    connection.cmd = cmd
    try:
        rc, output = connection.run()
    except Exception as e:
        return 1, [str(e)]
    return int(rc), output if output else []


# ---------------------------------------------------------------------------
# Main workflow functions
# ---------------------------------------------------------------------------

def _resolve_latest_backup(module, connection, backup_dir):
    """
    Run ``_build_latest_cmd`` on the controller and return the resolved path.

    Fails with a descriptive message when:
    - the command returns a non-zero exit code (e.g. backup_dir is empty)
    - the command output is blank after stripping whitespace
    """
    cmd = _build_latest_cmd(backup_dir)
    lines = _run_command(module, connection, cmd, "Resolve latest backup")
    latest = lines[0].strip() if lines else ""
    if not latest:
        module.fail_json(
            changed=False,
            msg=f"No backup entries found in '{backup_dir}'"
        )
    return latest


def run_nfs_backup(module, connection):
    """
    Execute the NFS external-backup workflow on the PowerVC Controller.

    The umount step is performed unconditionally — even when the copy fails —
    so the NFS share is never left permanently mounted.  Any copy failure is
    reported to Ansible only after the unmount has completed.

    Returns (latest_path: str, all_output_lines: list[str]).
    """
    backup_dir = module.params['backup_dir']
    nfs_server = module.params['nfs_server']
    nfs_export = module.params['nfs_export']
    mount_point = module.params['nfs_mount_point']
    nfs_options = module.params.get('nfs_options') or ''

    all_output = []

    # Step 0: resolve the latest backup entry before mounting anything
    latest_path = _resolve_latest_backup(module, connection, backup_dir)

    mkdir_cmd, mount_cmd, copy_cmd, umount_cmd = _build_nfs_commands(
        latest_path, nfs_server, nfs_export, mount_point, nfs_options
    )

    # Steps 1 & 2: setup — fail immediately on error (nothing to clean up yet)
    all_output.extend(_run_command(module, connection, mkdir_cmd,
                                   "Create mount point"))
    all_output.extend(_run_command(module, connection, mount_cmd,
                                   "Mount NFS share"))

    # Step 3: copy — run, but hold any failure until after cleanup
    copy_failure = None
    connection.cmd = copy_cmd
    try:
        copy_rc, copy_out = connection.run()
    except Exception as e:
        copy_failure = {"msg": f"Copy backup to NFS failed: {e}",
                        "rc": 1, "stderr": str(e)}
        copy_out = []
    else:
        copy_out = copy_out if copy_out else []
        if int(copy_rc) != 0:
            stderr_str = ("\n".join(copy_out)
                          if isinstance(copy_out, list) else str(copy_out))
            copy_failure = {
                "msg": f"Copy backup to NFS failed (rc={copy_rc})",
                "rc": int(copy_rc),
                "stderr": stderr_str,
            }
    all_output.extend(copy_out)

    # Step 4: unmount — always run regardless of copy outcome
    umount_rc, umount_out = _run_command_tolerant(connection, umount_cmd)
    all_output.extend(umount_out)

    # Surface any copy failure first (most actionable error)
    if copy_failure is not None:
        module.fail_json(changed=False, **copy_failure)

    # A failed umount after a successful copy is still a fatal error:
    # the NFS share would remain permanently mounted on the PowerVC node,
    # violating the core requirement of this feature.
    if umount_rc != 0:
        stderr_str = "\n".join(umount_out) if isinstance(umount_out, list) else str(umount_out)
        module.fail_json(
            changed=False,
            msg=f"umount of {mount_point} failed (rc={umount_rc}); "
                "NFS share may still be mounted — manual cleanup required",
            rc=umount_rc,
            stderr=stderr_str
        )

    return latest_path, all_output


def run_cos_backup(module, connection):
    """
    Execute the COS external-backup workflow on the PowerVC Controller.

    Returns (latest_path: str, all_output_lines: list[str]).
    """
    backup_dir = module.params['backup_dir']
    cos_endpoint = module.params['cos_endpoint']
    cos_bucket = module.params['cos_bucket']
    cos_access_key = module.params['cos_access_key']
    cos_secret_key = module.params['cos_secret_key']
    cos_prefix = module.params.get('cos_prefix') or ''

    # Resolve latest backup before uploading
    latest_path = _resolve_latest_backup(module, connection, backup_dir)

    cmd = _build_cos_command(
        latest_path, cos_endpoint, cos_bucket,
        cos_access_key, cos_secret_key, cos_prefix
    )
    output = _run_command(module, connection, cmd, "Upload backup to COS")
    return latest_path, output


def run_external_backup(module):
    """
    Entry point called by main().
    """
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    target_type = module.params['target_type']
    backup_dir = module.params['backup_dir']

    if target_type == 'nfs':
        _validate_nfs_params(module)
    else:
        _validate_cos_params(module)

    if module.check_mode:
        module.exit_json(
            changed=True,
            target_type=target_type,
            backup_dir=backup_dir,
            msg=(
                f"[CHECK MODE] Would copy latest backup from '{backup_dir}' "
                f"to external target '{target_type}'"
            )
        )

    # A single Connection object is reused across all remote commands.
    # connection.cmd is updated in _run_command before each run() call.
    connection = Connection(module, host_ip, user, password, command=None)

    if target_type == 'nfs':
        latest_path, all_output = run_nfs_backup(module, connection)
    else:
        latest_path, all_output = run_cos_backup(module, connection)

    module.exit_json(
        changed=True,
        target_type=target_type,
        backup_dir=backup_dir,
        latest_backup=latest_path,
        stdout_lines=all_output,
        msg=(
            f"External backup to '{target_type}' completed successfully "
            f"(latest backup: '{latest_path}')"
        )
    )


def main():
    """Main execution."""
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            backup_dir=dict(type='str', required=False,
                            default='/powervchome/backups'),
            target_type=dict(type='str', required=True,
                             choices=['nfs', 'cos']),
            # NFS parameters
            nfs_server=dict(type='str', required=False, default=None),
            nfs_export=dict(type='str', required=False, default=None),
            nfs_mount_point=dict(type='str', required=False,
                                 default='/mnt/powervc_external_backup'),
            nfs_options=dict(type='str', required=False, default=''),
            # COS parameters
            cos_endpoint=dict(type='str', required=False, default=None),
            cos_bucket=dict(type='str', required=False, default=None),
            cos_access_key=dict(type='str', required=False, default=None,
                                no_log=True),
            cos_secret_key=dict(type='str', required=False, default=None,
                                no_log=True),
            cos_prefix=dict(type='str', required=False, default=''),
        ),
        supports_check_mode=True
    )
    run_external_backup(module)


if __name__ == '__main__':
    main()
