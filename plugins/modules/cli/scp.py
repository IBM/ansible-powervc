#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: scp
author:
    - Yogita Garani (@yogita.garani1)
short_description: Copy files to PowerVC Controller using SCP
description:
  - This module copies files from the Ansible controller to the PowerVC Controller using SCP
  - Supports both file and directory transfers
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
  source:
    description:
      - Source file or directory path on Ansible controller
    required: true
    type: str
  destination:
    description:
      - Destination path on PowerVC Controller
    required: true
    type: str
  recursive:
    description:
      - Recursively copy directories
    required: false
    type: bool
    default: false
  state:
    description:
      - State of scp operation, always present
    type: str
    default: present
"""

EXAMPLES = """
---
- name: "Copy file to PowerVC"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Copy a file to PowerVC Controller"
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/local/path/file.txt"
        destination: "/remote/path/file.txt"
      register: result

    - name: "Show SCP result"
      debug:
        var: result


- name: "Copy directory to PowerVC"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Copy a directory to PowerVC Controller"
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/local/path/directory/"
        destination: "/remote/path/directory/"
        recursive: true
      register: result

    - name: "Show SCP result"
      debug:
        var: result


- name: "Copy backup file to PowerVC"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Copy backup archive to PowerVC"
      ibm.powervc.cli.scp:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        source: "/tmp/backup.tar.gz"
        destination: "/powervchome/backups/"
      register: result

    - name: "Show SCP result"
      debug:
        var: result
"""
from ansible.module_utils.basic import AnsibleModule
import pexpect
import os


def run_scp():
    """
    Read all arguments from the ansible module and execute SCP from the Ansible controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            state=dict(type='str', required=False, choices=[
                       'present'], default='present'),
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            source=dict(type='str', required=True),
            destination=dict(type='str', required=True),
            recursive=dict(type='bool', required=False, default=False),
        )
    )

    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    source = module.params['source']
    destination = module.params['destination']
    recursive = module.params['recursive']

    # Check if source exists
    if not os.path.exists(source):
        module.fail_json(msg=f"Source path does not exist: {source}", rc=1)

    # Check if source is a directory and recursive is not set
    if os.path.isdir(source) and not recursive:
        module.fail_json(
            msg=f"Source is a directory but recursive is not set: {source}", rc=1)

    # Construct SCP command
    host_key_ignore = "-O -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null"
    recursive_flag = "-r" if recursive else ""
    scp_command = f"scp {host_key_ignore} {recursive_flag} {source} {user}@{host_ip}:{destination}".strip()

    try:
        # Execute SCP command using pexpect for password handling
        child = pexpect.spawn(scp_command, timeout=300)

        # Expect password prompt and send password
        # Match pattern like "(user@ip) Password:"
        i = child.expect([r'Password:', pexpect.EOF, pexpect.TIMEOUT])

        if i == 0:
            # Password prompt received, send password
            child.sendline(password)
            child.expect(pexpect.EOF)
        elif i == 2:
            module.fail_json(msg="SCP operation timed out", rc=1)

        # Get exit status
        child.close()
        exit_code = child.exitstatus if child.exitstatus is not None else 0

        result = dict(
            changed=False,
            failed=False,
            rc=exit_code,
            msg='',
            source=source,
            destination=destination
        )

        if exit_code == 0:
            result['msg'] = f"Successfully copied {source} to {user}@{host_ip}:{destination}"
            result['failed'] = False
            result['changed'] = True
        else:
            result['msg'] = f"Failed to copy {source} to {user}@{host_ip}:{destination}"
            result['failed'] = True
            result['changed'] = False

        module.exit_json(**result)

    except pexpect.exceptions.TIMEOUT:
        module.fail_json(msg="SCP operation timed out", rc=1)
    except pexpect.exceptions.EOF:
        module.fail_json(msg="Unexpected end of SCP process", rc=1)
    except Exception as e:
        module.fail_json(msg=f"SCP operation failed: {str(e)}", rc=1)


def main():
    """
    Main execution
    """
    run_scp()


if __name__ == '__main__':
    main()
