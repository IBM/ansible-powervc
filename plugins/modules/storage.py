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
      - host_name or identifier of the storage system.
      - Used in fetching specific storage details, updating, and removing the storage.
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
    choices: [svc, hitachi, hpe, vmax_rest, purestorage, ds8k]
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
  detail:
    description:
      - When fetching storage systems (state=present without update/registration payload),
        retrieves comprehensive storage details including replication status, secondary/mirror
        storage details, volume pools, and capacities from the C(/storage-providers/detail) endpoint.
      - When set to C(false), queries the standard OpenStack C(/os-hosts) endpoint.
    type: bool
    default: false
  extra_params:
    description:
      - Dictionary for vendor-specific parameters.
      - For SVC / FlashSystem secondary storage and GMCV (Global Mirror with Change Volumes):
        - C(enable_mirror) (bool): Enable or disable secondary/mirror storage (C(true) or C(false)).
        - C(enable_gmcv) (bool): Enable or disable Global Mirror with Change Volumes (C(true) or C(false)).
        - C(mirror_access_ip) (str): IP address or hostname of the secondary SVC/FlashSystem storage.
        - C(mirror_pool) (str): Storage pool name on the secondary SVC storage system.
        - C(mirror_user_id) (str): Username for authenticating with the secondary SVC storage system.
        - C(mirror_password) (str): Password for secondary SVC storage system (automatically masked).
        - C(mirror_private_key_data) (str): SSH private key data for secondary SVC storage system (automatically masked).
      - For Hitachi:
        - C(rest_api_ip) (str): IP of the Hitachi REST API server.
        - C(rest_api_port) / C(port) (int): Port for REST API (default 443 or 23451).
        - C(hitachi_ldev_start) (int): Starting LDEV ID.
        - C(hitachi_ldev_end) (int): Ending LDEV ID.
        - C(hitachi_thin_pool) (str): Hitachi thin pool name.
        - C(default_fc_ports) (list): List of default FC ports (e.g. ['CL1-A']).
        - C(target_fc_ports) (list): List of target FC ports.
        - C(auto_add_certificate) (bool): Automatically add SSL certificate.
      - For HPE:
        - C(port) (int): Port for connection (default 443).
      - For PowerMAX:
        - C(port) / C(ssh_port) (int): Port for connection (default 8443).
        - C(storage_array_id) (str): Storage array ID (e.g. '000120000').
        - C(auto_add_certificate) (bool): Automatically add SSL certificate.
    type: dict
'''

EXAMPLES = r'''
# Get all storage systems (standard OpenStack summary)
- name: Get storage systems
  ibm.powervc.storage:
    cloud: powervc

# Get all storage systems with full PowerVC details (including secondary storage and replication)
- name: Get all storage providers with full details
  ibm.powervc.storage:
    cloud: powervc
    detail: true

# Get specific storage provider with full details
- name: Get storage provider by host name with full details
  ibm.powervc.storage:
    cloud: powervc
    id: "id12ms_tier1_3"
    detail: true

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

# Update SVC storage to enable secondary mirror storage and GMCV
- name: Configure secondary storage and enable mirroring on SVC
  ibm.powervc.storage:
    cloud: powervc
    state: present
    id: "id12ms_tier1_3"
    restart: false
    extra_params:
      enable_mirror: true
      enable_gmcv: true
      mirror_access_ip: "192.168.100.23"
      mirror_pool: "general-flash-1"
      mirror_user_id: "superuser"
      mirror_private_key_data: "{{ lookup('file', '~/.ssh/id_rsa') }}"

# Update SVC storage to disable mirroring
- name: Disable mirroring on SVC storage
  ibm.powervc.storage:
    cloud: powervc
    state: present
    id: "tier1_3"
    restart: false
    extra_params:
      enable_mirror: false
      enable_gmcv: false

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


SENSITIVE_EXTRA_PARAMS = {
    "mirror_password",
    "mirror_private_key_data",
    "password",
    "private_key_data",
    "ssh_key",
    "user_password",
}


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
        detail=dict(type="bool", default=False),
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
        extra = self.params.get("extra_params") or {}
        detail = self.params.get("detail", False)

        # Mask sensitive keys inside extra_params so they are never leaked in logs
        for sec_key in SENSITIVE_EXTRA_PARAMS:
            sec_val = extra.get(sec_key)
            if sec_val and isinstance(sec_val, (str, bytes)):
                if hasattr(self, "no_log_values") and isinstance(self.no_log_values, set):
                    self.no_log_values.add(sec_val)
                elif hasattr(self, "_no_log_values") and isinstance(self._no_log_values, set):
                    self._no_log_values.add(sec_val)

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
        is_check_mode = getattr(self.ansible, "check_mode", False) or getattr(self, "check_mode", False)
        if is_check_mode:
            if state == "absent":
                if not storage_id:
                    self.fail_json(msg="host name from storage specific metadata is required")
                self.exit_json(changed=True, msg=f"[CHECK MODE] Would remove storage system {storage_id}")
            elif state == "present" and not storage_id and host:
                self.exit_json(changed=True, msg=f"[CHECK MODE] Would register {stype} storage system {host}")
            elif state == "present" and storage_id and body:
                self.exit_json(changed=True, msg=f"[CHECK MODE] Would update storage system {storage_id}")

        result = storage_ops(
            module=self,
            endpoint=endpoint,
            authtoken=authtoken,
            tenant_id=tenant_id,
            verify=verify,
            state=state,
            storage_id=storage_id,
            body=body,
            detail=detail,
        )
        self.exit_json(**result)


def main():
    module = StorageModule()
    module()


if __name__ == "__main__":
    main()
