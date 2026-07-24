#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: database_operation
author:
    - Yogita Garani (@yogita.garani1)
short_description: Execute read-only queries on MariaDB or MongoDB on PowerVC
description:
  - This module executes read-only queries against MariaDB or MongoDB running
    on the PowerVC Controller over SSH using the C(powervc-dbop) CLI tool.
  - The C(collection) parameter is only valid for C(type=mongodb).
    Supplying it with C(type=mariadb) is an invalid combination and the
    module will fail with a descriptive error.
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
      - Type of database to execute the query against.
        Use C(mariadb) for MariaDB or C(mongodb) for MongoDB.
    required: false
    type: str
    choices: ['mongodb', 'mariadb']
    default: mariadb
  database:
    description:
      - Name of the database to query.
    required: true
    type: str
  collection:
    description:
      - Name of the MongoDB collection to query.
        Only valid when C(type=mongodb). Mutually exclusive with C(type=mariadb).
    required: false
    type: str
  query:
    description:
      - The query string to execute. For MariaDB this is SQL;
        for MongoDB this is a JSON query expression.
        Multiple statements may be C(;)-separated.
    required: true
    type: str
'''

EXAMPLES = '''
- name: "PowerVC Database Operations - MongoDB"
  hosts: localhost
  vars_files:
    - ../vars/powervc.yml
    - ../vars/secret.yml
  tasks:
    - name: "Query MongoDB collection"
      ibm.powervc.cli.database_operation:
        login_host: "{{ ipaddress }}"
        login_user: "{{ pvc_user }}"
        login_password: "{{ pvcroot_password }}"
        type: "mongodb"
        database: "{{ database }}"
        collection: "{{ collection }}"
        query: "{{ query }}"
      register: result
    - name: "Show output"
      debug:
        var: result

- name: "PowerVC Database Operations - MariaDB"
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
        type: "mariadb"
        database: "{{ database }}"
        query: "{{ query }}"
      register: result
    - name: "Show output"
      debug:
        var: result
'''

RETURN = '''
changed:
  description: Whether the query executed successfully.
  returned: always
  type: bool
rc:
  description: Return code from the database command.
  returned: always
  type: int
stdout_lines:
  description: Query output split into a list of lines.
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


def construct_command(db_type, db, query, collection):
    '''
    Construct the powervc-dbop command from the given parameters.

    :param str db_type: 'mariadb' or 'mongodb'
    :param str db: database name
    :param str query: query string
    :param str collection: MongoDB collection name (None for MariaDB)
    :return tuple(str|None, dict): (command, messages)
    '''
    # collection is only valid for MongoDB — caller must validate before here,
    # but return None so run_db_operation() can fail with a clear message.
    if collection is not None and db_type == "mariadb":
        return None, {}

    command = f"powervc-dbop {db_type} -d={db}"
    if collection is not None and db_type == "mongodb":
        command += f" -c={collection}"
    command += f" -q=\"{query}\""
    return command, {}


def run_db_operation(module):
    '''
    Execute the database query command on the PowerVC Controller.

    :param module: AnsibleModule instance
    '''
    host_ip = module.params['login_host']
    user = module.params['login_user']
    password = module.params['login_password']
    db_type = module.params['type']
    database = module.params['database']
    collection = module.params['collection']
    query = module.params['query']

    command, messages = construct_command(db_type, database, query, collection)

    # collection + mariadb is an invalid combination — fail with a clear message
    if command is None:
        module.fail_json(
            changed=False,
            msg=f"The 'collection' parameter is only valid for type=mongodb, "
                f"not for type={db_type}"
        )

    # check_mode: read-only query; no changes would occur regardless
    if module.check_mode:
        module.exit_json(
            changed=False,
            msg=f"[CHECK MODE] Would run: {command}"
        )

    connection = Connection(module, host_ip, user,
                            password, command=command, messages=messages)
    try:
        rc, output = connection.run()
    except Exception as e:
        module.fail_json(changed=False, msg=str(e))

    if int(rc) != 0:
        module.fail_json(
            msg=f"Database operation failed with rc={rc}",
            rc=int(rc),
            stderr=output,
            changed=False
        )

    if not output:
        module.warn("Database operation returned no output")

    # Database queries are read-only — they never mutate state
    module.exit_json(
        changed=False,
        rc=int(rc),
        stdout_lines=output if output else [],
        msg="Database operation completed successfully"
    )


def main():
    '''
    Main execution
    '''
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
        ),
        supports_check_mode=True
    )
    run_db_operation(module)


if __name__ == '__main__':
    main()
