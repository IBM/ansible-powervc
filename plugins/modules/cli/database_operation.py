#!/usr/bin/python
ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = """
---
module: database_operation
author:
    - Yogita Garani (@yogita.garani1)
short_description: Database Operations
description:
  - This module executes read only queries on Mariadb and Mongodb
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
  type:
    description:
      - Type of database to execut the query (mongodb, mariadb)
    required: true
    type: str
  db:
    description:
      - Database to query
    required: true
    type: str
  collection:
    description:
      - Name of the mongodb collection
    type: str
  mode:
    description:
      - ';' separated queries
    type: str
"""

EXAMPLES = """
---
- name: "PowerVC Database Operations"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Query MongoDB"
      ibm.powervc.cli.database_operation:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        type: mongodb
        database: "{{ database }}"
        collection: "{{ collection }}"
        query: "{{ query }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result

---
- name: "PowerVC Database Operations"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml

  tasks:
    - name: "Query MariaDB"
      ibm.powervc.cli.database_operation:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        type: mariadb
        database: "{{ database }}"
        query: "{{ query }}"
      register: result

    - name: "Show stdout"
      debug:
        var: result
"""

from ansible_collections.ibm.powervc.plugins.module_utils.connection import Connection
from ansible_collections.ibm.powervc.plugins.module_utils.errors import CLIError
from ansible.module_utils.basic import AnsibleModule


def construct_command(db_type, db, query, collection):
    """
    Construct the command based on the parameters

    :param str db_type: MariaDB or MongoDB
    :param str db: Database to run the query on
    :param str query: ';' separated queries to run
    :param str collection: Mongodb collection
    :return str, dict command, messages: Return the constructed command and its messages
    """
    messages = {}
    command = None
    if collection is not None and db_type == "mariadb":
        return command, messages
    command = f"powervc-dbop {db_type} -d={db}"
    if collection is not None and db_type == "mongodb":
        command += f" -c={collection}"
    command += f" -q=\"{query}\""
    return command, messages


def run_cli_command():
    """
    Read all arguments from the ansible module and execute the command on the controller
    """
    module = AnsibleModule(
        argument_spec=dict(
            login_host=dict(type='str', required=True),
            login_user=dict(type='str', required=True),
            login_password=dict(type='str', required=True, no_log=True),
            type=dict(type='str', required=False, default="mariadb",
                      choices=['mongodb', 'mariadb']),
            database=dict(type='str', required=True),
            collection=dict(type='str', required=False, default=None),
            query=dict(type='str', required=True),

        )
    )
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    db_type = module.params['type']
    database = module.params['database']
    collection = module.params['collection']
    query = module.params['query']
    output = None
    changed = False
    failed = True

    command, messages = construct_command(db_type, database, query, collection)
    if command is None and not messages:
        module.fail_json(failed=True, changed=False, msg="Wrong arguments")

    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
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
        module.fail_json(failed=True, msg=msg)
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
        result['msg'] = "Database operation completed successfully"
    else:
        result['warning'] = output
        result['msg'] = "Database operation did not complete successfully"
    module.exit_json(**result)


def main():
    """
    Main execution
    """
    run_cli_command()


if __name__ == '__main__':
    main()
