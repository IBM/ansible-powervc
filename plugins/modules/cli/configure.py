#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: configure
author:
    - Yogita Garani (@yogita.garani1)
short_description: Configure PowerVC
description:
  - This module performs configure operation on the PowerVC Controller
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
  cluster:
    description:
      - Cluster Name
    required: true
    type: str
  validate:
    description:
      - Validate post configure
    type: boolean
  force:
    description:
      - Force configure PowerVC
    type: boolean
  verbose:
    description:
      - Configure PowerVC with verbose logging
    type: boolean
"""

EXAMPLES = """
- name: "Ansible SDK PowerVC CLI Example"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Configure PowerVC"
      ibm.powervc.cli.configure:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result
    - name: "Show stdout"
      debug:
        var: result


- name: "Ansible SDK PowerVC CLI Example"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Configure PowerVC and validate"
      ibm.powervc.cli.configure:
        validate: True
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result
    - name: "Show stdout"
      debug:
        var: result


- name: "Ansible SDK PowerVC CLI Example"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Configure PowerVC in verbose mode"
      ibm.powervc.cli.configure:
        verbose: True
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result
    - name: "Show stdout"
      debug:
        var: result


- name: "Ansible SDK PowerVC CLI Example"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Force Configure PowerVC"
      ibm.powervc.cli.configure:
        force: True
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        cluster: "{{ cluster_name }}"
      register: result
    - name: "Show stdout"
      debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection \
    import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(cluster_name, validate=None, force=None, verbose=None):
    """
    Construct the command based on the parameters

    :param str cluster_name: cluster name
    :param str validate: Validate after configure
    :param str force: Force configure
    :param str verbose: Configure in verbose mode
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {}
    command = None
    if force is not None:
        command = f"powervc-opsmgr configure -c {cluster_name} -f"
    elif verbose is not None:
        command = f"powervc-opsmgr configure -c {cluster_name} -v"
    elif validate is not None:
        command = f"powervc-opsmgr configure -c {cluster_name} -pv"
    else:
        command = f"powervc-opsmgr configure -c {cluster_name}"
    return command, messages

# Execution


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            cluster=dict(type='str', required=True),
            validate=dict(type='bool', required=False),
            verbose=dict(type='bool', required=False),
            force=dict(type='bool', required=False),
            state=dict(type='str', required=False, default='present'),
        )
    )
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    validate = module.params['validate']
    verbose = module.params['verbose']
    force = module.params['force']
    cluster_name = module.params['cluster']

    command, messages = construct_command(cluster_name, validate, force, verbose)

    output = None
    changed = False

    if command is None and not messages:
        module.fail_json(failed=True, msg="Wrong arguments")

    connection = Connection(module, host_ip, user, password, command=command, messages=messages)
    try:
        rc, output = connection.run()
        if int(rc) != 0:
            changed = False
            failed = True
        else:
            changed = True
            failed = False
    except (CLIError, Exception) as e:
        msg = str(e)
        module.fail_json(msg=msg)
    result = dict(
        changed=False,
        failed=True,
        warning=False,
        stdout_lines="",
        error="",
        rc=1,
        msg=''
    )
    result['changed'] = changed
    result['failed'] = failed
    result['rc'] = int(rc)

    if output and rc == 0:
        result['stdout_lines'] = output
        result['msg'] = "Configure operation completed successfully"
    else:
        result['warning'] = output
        result['msg'] = "Configure operation did not complete successfully"
    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
