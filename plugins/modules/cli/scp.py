#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: scp
author:
    - Yogita Garani (@yogita.garani1)
short_description: Copy files to PowerVC Controller using SFTP
description:
  - This module copies files from the Ansible controller to the PowerVC Controller
    using Paramiko's SFTP — no subprocess, password never on the command line.
  - Supports both single-file and recursive directory transfers.
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
  source:
    description:
      - Source file or directory path on the Ansible controller
    required: true
    type: str
  destination:
    description:
      - Destination path on the PowerVC Controller
    required: true
    type: str
  recursive:
    description:
      - Recursively copy directories (required when C(source) is a directory)
    required: false
    type: bool
    default: false
  login_port:
    description:
      - SSH port on the PowerVC Controller
    required: false
    type: int
    default: 22
'''

EXAMPLES = '''
- name: Copy file to PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Copy a single file to PowerVC Controller
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/local/path/file.txt"
        destination: "/remote/path/file.txt"
      register: result

    - name: Display SCP result
      debug:
        var: result


- name: Copy directory to PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Copy a directory recursively to PowerVC Controller
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/local/path/directory/"
        destination: "/remote/path/directory/"
        recursive: true
      register: result

    - name: Display directory copy result
      debug:
        var: result


- name: Copy backup archive to PowerVC
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: Copy backup tarball to PowerVC backups directory
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/tmp/backup.tar.gz"
        destination: "/powervchome/backups/"
      register: result

    - name: Display backup copy result
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the file was successfully copied
  returned: always
  type: bool
source:
  description: Source path that was copied
  returned: always
  type: str
destination:
  description: Destination path on the remote host
  returned: always
  type: str
bytes_transferred:
  description: Total bytes transferred (files only; 0 for directories)
  returned: success
  type: int
'''

import os
import paramiko
from ansible.module_utils.basic import AnsibleModule


def _sftp_put_file(sftp, local_path, remote_path):
    '''Upload a single file and return bytes transferred.'''
    sftp.put(local_path, remote_path)
    return os.path.getsize(local_path)


def _sftp_mkdir_p(sftp, remote_dir):
    '''Create remote directory and all missing parents (like mkdir -p).'''
    parts = remote_dir.replace('\\', '/').split('/')
    current = ''
    for part in parts:
        if not part:
            current = '/'
            continue
        current = current.rstrip('/') + '/' + part
        try:
            sftp.stat(current)
        except IOError:
            sftp.mkdir(current)


def _sftp_put_dir(sftp, local_dir, remote_dir):
    '''Recursively upload a directory tree. Returns total bytes transferred.'''
    _sftp_mkdir_p(sftp, remote_dir)
    total = 0
    for entry in os.listdir(local_dir):
        local_entry = os.path.join(local_dir, entry)
        remote_entry = remote_dir.rstrip('/') + '/' + entry
        if os.path.isdir(local_entry):
            total += _sftp_put_dir(sftp, local_entry, remote_entry)
        else:
            total += _sftp_put_file(sftp, local_entry, remote_entry)
    return total


def run_scp(module):
    '''Transfer files to PowerVC using Paramiko SFTP (no subprocess, no pexpect).'''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    source = module.params['source']
    destination = module.params['destination']
    recursive = module.params['recursive']
    port = module.params['login_port']

    if not os.path.exists(source):
        module.fail_json(msg=f"Source path does not exist: {source}")

    if os.path.isdir(source) and not recursive:
        module.fail_json(
            msg=f"Source is a directory but recursive=false: {source}"
        )

    if module.check_mode:
        module.exit_json(
            changed=True,
            msg=f"[CHECK MODE] Would copy {source} to {host_ip}:{destination}",
            source=source,
            destination=destination,
            bytes_transferred=0
        )

    transport = None
    try:
        transport = paramiko.Transport((host_ip, port))
        transport.connect(username=user, password=password)
        sftp = paramiko.SFTPClient.from_transport(transport)

        if os.path.isdir(source):
            bytes_sent = _sftp_put_dir(sftp, source, destination)
        else:
            bytes_sent = _sftp_put_file(sftp, source, destination)

        sftp.close()

    except paramiko.AuthenticationException as e:
        module.fail_json(msg=f"SSH authentication failed: {e}")
    except paramiko.SSHException as e:
        module.fail_json(msg=f"SSH error during transfer: {e}")
    except IOError as e:
        module.fail_json(msg=f"File transfer error: {e}")
    except Exception as e:
        module.fail_json(msg=f"Unexpected error during transfer: {e}")
    finally:
        if transport is not None:
            transport.close()

    module.exit_json(
        changed=True,
        msg=f"Successfully copied {source} to {user}@{host_ip}:{destination}",
        source=source,
        destination=destination,
        bytes_transferred=bytes_sent
    )


def main():
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            source=dict(type='str', required=True),
            destination=dict(type='str', required=True),
            recursive=dict(type='bool', required=False, default=False),
            login_port=dict(type='int', required=False, default=22),
        ),
        supports_check_mode=True
    )

    run_scp(module)


if __name__ == '__main__':
    main()
