#!/usr/bin/python

DOCUMENTATION = r'''
---
module: storage
short_description: Manage storage systems in PowerVC
description:
  - Register, update, delete, or retrieve storage systems in PowerVC.
  - Supports multiple storage types like Storwize, Hitachi, HPE, DS8000, Pure and PowerMAX.
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
options:
  state:
    description:
      - Desired state of the storage.
    type: str
    choices: [present, absent]
    default: present
  id:
    description:
      - host_name of the storage system.
      - Used in fetching the storage details and for removing the storage
    type: str
  host:
    description:
      - IP address or hostname of the storage system.
    type: str
  user:
    description:
      - Username for storage authentication.
    type: str
  password:
    description:
      - Password for storage authentication.
    type: str
    no_log: true
  ssh_key:
    description:
      - Private key for authentication.
    type: str
    no_log: true
  type:
    description:
      - Type of storage system.
    type: str
    choices: [svc, hitachi, hpe, powermax, purestorage, ds8k]
  volume_pool:
    description:
      - Storage pool name.
    type: str
  name:
    description:
      - Display name of the storage system.
    type: str
  auto_add_host_key:
    description:
      - Automatically add SSH host key.
    type: bool
    default: true
  extra_params:
    description:
      - Dictionary for vendor-specific parameters.
      - For Hitachi, requires C(port) (default 23451), C(rest_api_ip), C(hitachi_ldev_start), and C(hitachi_ldev_end).
      - For HPE, supports C(port) (default 443).
      - For PowerMAX, supports C(port) (default 8443).
    type: dict
'''

EXAMPLES = r'''
# Get all storage systems
- name: Get storage
  ibm.powervc.storage:
    cloud: powervc

# Get specific storage
- name: Get storage by id
  ibm.powervc.storage:
    cloud: powervc
    name: storage123

# Register SVC storage
- name: Register SVC storage
  ibm.powervc.storage:
    cloud: powervc
    state: present
    type: svc
    host: 1.2.4.5
    user: superuser
    password: passw0rd
    volume_pool: Pool0
    name: SVC-1.2.4.5

# Register Hitachi storage
- name: Register Hitachi storage
  ibm.powervc.storage:
    cloud: powervc
    state: present
    type: hitachi
    host: 1.2.3.4
    user: user
    password: passw0rd
    volume_pool: PowerVC1
    name: Hitachi
    extra_params:
      auto_add_certificate: true
      rest_api_ip: 1.2.3.4
      port: 23451
      hitachi_ldev_start: 2000
      hitachi_ldev_end: 3000
      default_fc_ports:
        - CL1-A
      target_fc_ports:
        - CL1-A
      hitachi_thin_pool: Pool0

# Register PowerMAX storage
- name: Register PowerMAX storage
  ibm.powervc.storage:
    cloud: powervc
    state: present
    type: vmax_rest
    host: 20.20.20.20
    user: admin
    password: password
    volume_pool: Pool2
    host_display_name: PowerMAX-Storage
    extra_params:
      auto_add_certificate: true
      port: 8443
      storage_array_id: "000120000"

# Delete storage
- name: Delete storage
  ibm.powervc.storage:
    cloud: powervc
    host: storage123
    state: absent
'''

from ansible_collections.ibm.powervc.plugins.module_utils.crud_storage import (
    storage_ops,
    get_endpoint_url_by_service_name,
)
from ansible_collections.openstack.cloud.plugins.module_utils.openstack import (
    OpenStackModule,
)


class StorageModule(OpenStackModule):
    argument_spec = dict(
        state=dict(type="str", choices=["present", "absent"], default="present"),
        id=dict(type="str"),
        host=dict(type="str"),
        user=dict(type="str"),
        password=dict(type="str", no_log=True),
        ssh_key=dict(type="str", no_log=True),
        type=dict(type="str", choices=["svc", "hitachi", "hpe", "vmax_rest", "ds8k", "purestorage"]),
        volume_pool=dict(type="str"),
        name=dict(type="str"),
        auto_add_host_key=dict(type="bool", default=True),
        extra_params=dict(type="dict", default={}),
        restart=dict(type="bool"),
    )
    module_kwargs = dict(supports_check_mode=True)

    def run(self):
        state = self.params.get("state")
        storage_id = self.params.get("id")
        host = self.params.get("host")
        user = self.params.get("user")
        password = self.params.get("password")
        private_key_data = self.params.get("ssh_key")
        stype = self.params.get("type")
        volume_pool = self.params.get("volume_pool")
        display_name = self.params.get("name")
        auto_add = self.params.get("auto_add_host_key")
        extra = self.params.get("extra_params")
        authtoken = self.conn.auth_token
        tenant_id = self.conn.session.get_project_id()
        validate_certs = self.params.get("validate_certs")
        if validate_certs is False:
            self.conn.session.verify = False
        verify = self.conn.session.verify
        restart = self.params.get("restart")
        endpoint = get_endpoint_url_by_service_name(
            self, self.conn, "volume", tenant_id
        )
        body = None
        if state == "present" and not storage_id and host:
            registration = {
                "host_type": stype,
                "access_ip": host,
                "user_id": user,
                "auto_add_host_key": auto_add,
                "volume_pool_name": volume_pool,
                "host_display_name": display_name,
            }
            if password:
                registration["password"] = password
            if private_key_data:
                registration["private_key_data"] = private_key_data
            # Hitachi
            if stype == "hitachi":
                # Supported extra_params examples:
                # rest_api_ip
                # rest_api_port
                # hitachi_ldev_start
                # hitachi_ldev_end
                # default_fc_ports
                # target_fc_ports
                # hitachi_thin_pool
                # auto_add_certificate
                rest_api_port = extra.get("rest_api_port", 443)
                extra["rest_api_port"] = rest_api_port
            # PowerMax port mandatory, default 443
            if stype == "vmax_rest":
                # Supported extra_params examples:
                # ssh_port
                # storage_array_id
                # auto_add_certificate
                ssh_port = extra.get("ssh_port", 8443)
                extra["ssh_port"] = ssh_port
            if stype == "hpe":
                # port
                port = extra.get("port", 443)
                extra["port"] = port
            registration.update(extra)
            body = {
                "host": {
                    "registration": registration
                }
            }
        elif state == "present" and storage_id:
            update_fields = {}
            if host:
                update_fields["access_ip"] = host
            if user:
                update_fields["user_id"] = user
            if password:
                update_fields["password"] = password
            if private_key_data:
                update_fields["private_key_data"] = private_key_data
            if volume_pool:
                update_fields["volume_pool_name"] = volume_pool
            if display_name:
                update_fields["host_display_name"] = display_name
            if restart:
                update_fields["restart"] = restart
            update_fields.update(extra)
            if update_fields:
                body = {
                    "registration": update_fields
                }
        result = storage_ops(
            module=self,
            endpoint=endpoint,
            authtoken=authtoken,
            tenant_id=tenant_id,
            verify=verify,
            state=state,
            storage_id=storage_id,
            body=body,
        )
        self.exit_json(**result)


def main():
    module = StorageModule()
    module()


if __name__ == "__main__":
    main()
