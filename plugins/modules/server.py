#!/usr/bin/python

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'PowerVC'}


DOCUMENTATION = '''
---
module: server
author:
    - Karteesh Kumar Vipparapelli (@vkarteesh)
short_description: Create/Delete the Virtual Machines from PowerVC.
description:
  - This playbook helps in performing the Create and Delete VM operations.
options:
  name:
    description:
      - Name of the Server
    type: str
  flavor:
    description:
      - Name of the flavor
    type: str
  image:
    description:
      - Name of the image
    type: str
  host:
    description:
      - MTMS of the host
    type: str
  collocation_rule_name:
    description:
      - Name of the collocation_rule_name
    type: str
  max_count:
    description:
      - The maximum number of servers to create.
    type: str
  scg_id:
    description:
      - ID of the Storage Connectivity Group.
    type: str
  virtual_serial_number:
    description:
      - Virtual Serial Number (VSN) to be assigned to the VM.
      - Valid values are C(auto), C(none), or a valid 7-character alpha-numeric VSN.
    type: str
  key_name:
    description:
      - The key pair name to be used when creating a instance.
    type: str
  user_data:
    description:
      - activation_input data which is passed to the instance.
    type: str
  network:
     description:
       - Name or ID of a network to attach this instance to. A simpler
         version of the I(nics) parameter, only one of I(network) or I(nics)
         should be supplied.
       - This server attribute cannot be updated.
     type: str
  nics:
     description:
       - A list of networks to which the instance's interface should
         be attached. Networks may be referenced by network_id/network_name
     type: list
     elements: raw
     default: []
  image_volume_override:
     description:
       - A list of volume id and templated id which will be attached to the VM.
         Referenced by volume_id and template_id.
     type: list
     elements: raw
     default: []
  volume_name:
     description:
       - A list of volumes that are to be attached to the VM
     type: list
     elements: raw
     default: []
  pmem_volume:
    description:
      - List of Persistent Memory (PMEM) volumes to attach to the VM.
    type: list
    elements: dict
  affinity:
    description:
      - Affinity settings for VM placement.
    type: dict
    suboptions:
      score:
        description:
          - Minimum affinity score required for VM placement.
          - Valid values are integers from 0 to 100.
        type: int
      action:
        description:
          - Action to take when the minimum affinity score cannot be satisfied.
        type: str
        choices:
          - warn
          - fail
          - none
  state:
    description:
      - VM Operation to be performed
    choices: [absent, present]
    required: yes
    type: str
'''

EXAMPLES = '''
  - name: PowerVC Create VM Playbook
    hosts: localhost
    gather_facts: no
    vars:
     auth:
      auth_url: https://<POWERVC>:5000/v3
      project_name: PROJECT-NAME
      username: USERID
      password: PASSWORD
      project_domain_name: PROJECT_DOMAIN_NAME
      user_domain_name: USER_DOMAIN_NAME
      - name: Create a new instance and attaches to a network
        ibm.powervc.server:
          auth: "{{ auth }}"
          name: "VM_NAME"
          image: "VM_IMAGE"
          host: "HOST_ID"
          timeout: 200
          max_count: "COUNT"
          collocation_rule_name: "COLLOCATION_RULE_NAME"
          nics:
            - network_name: "NETWORK_NAME"
              fixed_ip: "FIXED_IP" # "fixed_ip: 192.168.10.20"
          image_volume_override:
            - volume_id: "VOLUME_ID"
              template_id: "TEMPLATE_ID"
          flavor: "FLAVOR_NAME"
          volume_name: ["VOLUME_1","VOLUME_2"]
          state: present
          validate_certs: no
        register: result
      - name: Display server info
        debug: var=result

  - name: PowerVC Create VM Playbook
    hosts: localhost
    gather_facts: no
      - name: Create a new instance and attaches to a network
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          host: "HOST_ID"
          timeout: 200
          max_count: "COUNT"
          collocation_rule_name: "COLLOCATION_RULE_NAME"
          user_data: |
            #!/bin/sh
            apt update
            apt -y full-upgrade
          nics:
            - network_name: "NETWORK_NAME"
              fixed_ip: "FIXED_IP" # "fixed_ip: 192.168.10.20"
          image_volume_override:
            - volume_id: "VOLUME_ID"
              template_id: "TEMPLATE_ID"
          flavor: "FLAVOR_NAME"
          volume_name: ["VOLUME_1","VOLUME_2"]
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug: var=result

  - name: PowerVC Create VM Playbook with Storage Connectivity Group
    hosts: localhost
    gather_facts: no
      - name: Create a new instance and attaches to a network
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          host: "HOST_ID"
          timeout: 200
          max_count: "COUNT"
          collocation_rule_name: "COLLOCATION_RULE_NAME"
          scg_id: "STORAGE_CONNECTIVITY_GROUP_ID"
          nics:
            - network_name: "NETWORK_NAME"
              fixed_ip: "FIXED_IP" # "fixed_ip: 192.168.10.20"
          image_volume_override:
            - volume_id: "VOLUME_ID"
              template_id: "TEMPLATE_ID"
          flavor: "FLAVOR_NAME"
          volume_name: ["VOLUME_1","VOLUME_2"]
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug: var=result

  - name: PowerVC Create VM Playbook with Storage Connectivity Group
    hosts: localhost
    gather_facts: no
      - name: Create a new instance and attaches to a network
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          host: "HOST_ID"
          timeout: 200
          max_count: "COUNT"
          collocation_rule_name: "COLLOCATION_RULE_NAME"
          scg_id: "STORAGE_CONNECTIVITY_GROUP_ID"
          nics:
            - network_name: "NETWORK_NAME"
              fixed_ip: "FIXED_IP" # "fixed_ip: 192.168.10.20"
          image_volume_override:
            - volume_id: "VOLUME_ID"
              template_id: "TEMPLATE_ID"
          flavor: "FLAVOR_NAME"
          volume_name: ["VOLUME_1","VOLUME_2"]
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug: var=result

  - name: PowerVC Create VM Playbook with custom VSN
    hosts: localhost
    gather_facts: no
    tasks:
      - name: Create VM with custom VSN
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          flavor: "FLAVOR_NAME"
          host: "HOST_ID"
          virtual_serial_number: "ABCD001"
          nics:
            - network_name: "NETWORK_NAME"
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug:
          var: result

  - name: PowerVC Create VM Playbook with auto VSN
    hosts: localhost
    gather_facts: no
    tasks:
      - name: Create VM with auto VSN
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          flavor: "FLAVOR_NAME"
          host: "HOST_ID"
          virtual_serial_number: "auto"
          nics:
            - network_name: "NETWORK_NAME"
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug:
          var: result

  - name: PowerVC Create VM Playbook with Persistent memory
    hosts: localhost
    gather_facts: no
    tasks:
      - name: Create VM with auto VSN
        ibm.powervc.server:
          cloud: "CLOUD_NAME"
          name: "VM_NAME"
          image: "VM_IMAGE"
          flavor: "FLAVOR_NAME"
          host: "HOST_ID"
          nics:
            - network_name: "NETWORK_NAME"
          pmem_volume:
           - name: pmem1
             size: 256
             affinity: true
             device: DRAM
           - name: pmem2
             size: 256
             affinity: false
             device: DRAM
          state: present
          validate_certs: false
        register: result
      - name: Display server info
        debug:
          var: result

  - name: Create VM with affinity score
    ibm.powervc.server:
      cloud: CLOUD_NAME
      name: VM_NAME
      image: IMAGE_NAME
      flavor: FLAVOR_NAME
      host: HOST_ID
      affinity:
        score: 80
        action: fail
      nics:
        - network_name: NETWORK_NAME
      state: present

  - name: PowerVC Delete VM Playbook
    hosts: localhost
    gather_facts: no
    vars:
     auth:
      auth_url: https://<POWERVC>:5000/v3
      project_name: PROJECT-NAME
      username: USERID
      password: PASSWORD
      project_domain_name: PROJECT_DOMAIN_NAME
      user_domain_name: USER_DOMAIN_NAME
      - name: Delete the VM based on the input name provided
        ibm.powervc.server:
          auth: "{{ auth }}"
          name: "VM_NAME"
          state: absent
        register: result
      - name: Display server info
        debug: var=result

'''


from ansible_collections.openstack.cloud.plugins.module_utils.openstack import OpenStackModule
from ansible_collections.ibm.powervc.plugins.module_utils.crud_server import server_ops, server_flavor, get_collocation_rules_id
import copy
import base64


class ServerOpsModule(OpenStackModule):
    argument_spec = dict(
        name=dict(),
        id=dict(),
        volume_id=dict(default=[], type='list', elements='str'),
        volume_name=dict(default=[], type='list', elements='str'),
        flavor=dict(),
        image=dict(),
        key_name=dict(),
        host=dict(),
        metadata=dict(type='raw', aliases=['meta']),
        nics=dict(default=[], type='list', elements='raw'),
        image_volume_override=dict(default=[], type='list', elements='raw'),
        network=dict(),
        user_data=dict(),
        max_count=dict(type='int'),
        collocation_rule_name=dict(),
        scg_id=dict(),
        virtual_serial_number=dict(required=False),
        pmem_volume=dict(default=[], type='list', elements='dict'),
        affinity=dict(
            type='dict',
            default={},
            options=dict(
                score=dict(type='int'),
                action=dict(
                    type='str',
                    choices=['warn', 'fail', 'none']
                )
            )
        ),
        security_groups=dict(default=[], type='list', elements='str'),
        state=dict(default='present', choices=['absent', 'present']),
    )
    module_kwargs = dict(
        supports_check_mode=True,
        mutually_exclusive=[
            ['name', 'id']
        ]
    )

    def _parse_nics(self):
        nics = []
        stringified_nets = self.params['nics']

        if not isinstance(stringified_nets, list):
            self.fail_json(msg="The 'nics' parameter must be a list.")

        nets = [(dict((nested_net.split('='),))
                for nested_net in net.split(','))
                if isinstance(net, str) else net
                for net in stringified_nets]

        for net in nets:
            if not isinstance(net, dict):
                self.fail_json(
                    msg="Each entry in the 'nics' parameter must be a dict.")
            if net.get('network_id'):
                nics.append({"uuid": net["network_id"]})
            elif net.get('network_name'):
                network_id = self.conn.network.find_network(
                    net['network_name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['network_name']
                net['uuid'] = network_id
                nics.append(net)
            elif net.get('fixed_ip'):
                nics.append(net)
            elif net.get('port_id'):
                nics.append({"port": net["port_id"]})
            elif net.get('port_name'):
                port_id = self.conn.network.find_port(
                    net['port_name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['port_name']
                net['port'] = port_id
                nics.append(net)

            if 'tag' in net:
                nics[-1]['tag'] = net['tag']
        return nics

    def _parse_image_volume_override(self):
        image_volume_override = []
        stringified_nets = self.params['image_volume_override']

        if not isinstance(stringified_nets, list):
            self.fail_json(msg="The 'image_volume_override' parameter must be a list.")

        nets = [(dict((nested_net.split('='),))
                for nested_net in net.split(','))
                if isinstance(net, str) else net
                for net in stringified_nets]

        for net in nets:
            if not isinstance(net, dict):
                self.fail_json(
                    msg="Each entry in the 'image_volume_override' parameter must be a dict.")
            if net.get('volume_id'):
                image_volume_override.append(net)
            elif net.get('net-name'):
                network_id = self.conn.network.find_network(
                    net['net-name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['net-name']
                net['uuid'] = network_id
                image_volume_override.append(net)
            elif net.get('template_id'):
                image_volume_override.append(net)
            elif net.get('port_id'):
                image_volume_override.append(net)
            elif net.get('port_name'):
                port_id = self.conn.network.find_port(
                    net['port-name'], ignore_missing=False).id
                net = copy.deepcopy(net)
                del net['port_name']
                net['port'] = port_id
                image_volume_override.append(net)

            if 'tag' in net:
                image_volume_override[-1]['tag'] = net['tag']
        return image_volume_override

    def run(self):
        try:
            authtoken = self.conn.auth_token
            vm_name = self.params['name']
            vmid = self.params['id']
            state = self.params['state']
            image = self.params['image']
            max_count = self.params['max_count']
            availability_zone = self.params['host']
            flavor = self.params['flavor']
            # security_groups = self.params['security_groups']
            collocation_rule = self.params['collocation_rule_name']
            # network = self.params['network']
            nics = self.params['nics']
            image_vol_template = self.params['image_volume_override']
            key_name = self.params['key_name']
            # meta = self.params['metadata']
            volume_name = self.params['volume_name']
            volume_id = self.params['volume_id']
            scg_id = self.params['scg_id']
            virtual_serial_number = self.params['virtual_serial_number']
            pmem_volume = self.params['pmem_volume']
            affinity = self.params.get('affinity')
            affinity_score = affinity.get('score')
            affinity_score_action = affinity.get('action')
            user_data = self.params['user_data']
            tenant_id = self.conn.session.get_project_id()
            if state == "present":
                flavor_id = self.conn.compute.find_flavor(flavor, ignore_missing=False).id
                imageRef = self.conn.compute.find_image(image, ignore_missing=False).id
                nics = self._parse_nics()
                if user_data:
                    base64_encoded = base64.b64encode(user_data.encode('utf-8'))
                    userdata = base64_encoded.decode('utf-8')
                else:
                    userdata = None
                if not volume_id:
                    vol_id = []
                    for name in volume_name:
                        vol_id.append(self.conn.block_storage.find_volume(name, ignore_missing=False).id)
                    vol_list = []
                    index = 1
                    for uuid in vol_id:
                        entry = {"boot_index": index, "delete_on_termination": False, "destination_type": "volume", "source_type": "volume", "uuid": uuid}
                        vol_list.append(entry)
                        index += 1
                    # vol_dict = {"block_device_mapping_v2": vol_list}
                elif volume_id:
                    vol_list = []
                    index = 1
                    for uuid in volume_id:
                        entry = {"boot_index": index, "delete_on_termination": False, "destination_type": "volume", "source_type": "volume", "uuid": uuid}
                        vol_list.append(entry)
                        index += 1
                    # vol_dict = {"block_device_mapping_v2": vol_list}

                volid = None  # Initialize with None
                template_id = None  # Initialize with None
                if image_vol_template:
                    volid = image_vol_template[0].get('volume_id', None)
                    template_id = image_vol_template[0].get('template_id', None)
                flavor = server_flavor(
                    self, self.conn, authtoken, tenant_id, flavor_id,
                    imageRef, volid, template_id, scg_id,
                    virtual_serial_number, pmem_volume,
                    affinity_score, affinity_score_action
                )
                collocation_rule_id = get_collocation_rules_id(self, self.conn, authtoken, tenant_id, collocation_rule)
                if availability_zone:
                    availability_zone = ":" + availability_zone

                uuid_value = None
                for nic in nics:
                    # If network_id/network_name was provided,
                    # _parse_nics() converts it to "uuid"
                    if nic.get("uuid"):
                        uuid_value = nic["uuid"]
                        break
                    # If port_id/port_name was provided,
                    # _parse_nics() converts it to "port"
                    if nic.get("port"):
                        port = self.conn.network.get_port(nic["port"])
                        if port:
                            uuid_value = port.network_id
                            break
                if not uuid_value:
                    self.fail_json(
                        msg="Unable to determine primary network from the provided NICs.",
                        changed=False
                    )
                vm_data = {"server": {
                           "name": vm_name,
                           "imageRef": imageRef,
                           "key_name": key_name,
                           "availability_zone": availability_zone,
                           "block_device_mapping_v2": vol_list,
                           "max_count": max_count,
                           "config_drive": True,
                           "user_data": userdata,
                           "networks": nics,
                           "metadata": {"primary_network": uuid_value},
                           "flavor": flavor},
                           "os:scheduler_hints": collocation_rule_id}
                res = server_ops(self, self.conn, authtoken, tenant_id, vm_name, state, vm_data, vm_id=None)
            elif state == "absent":
                vm_data = None
                res = server_ops(self, self.conn, authtoken, tenant_id, vm_name, state, vm_data, vm_id=vmid)
            self.exit_json(changed=True, result=res)
        except Exception as e:
            self.fail_json(msg=f"An unexpected error occurred: {str(e)}", changed=False)


def main():
    module = ServerOpsModule()
    module()


if __name__ == '__main__':
    main()
