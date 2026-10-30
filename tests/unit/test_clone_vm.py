import pytest   
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import clone_vm

TEST_VM_ID = "test_vm_id"
TEST_VM_NAME = "test_vm_name"
TEST_CLONE_VM_NAME = "test_clone_vm"
TEST_IMAGE_NAME = "test_image"
TEST_NETWORK_ID = "test_network_id"
TEST_PORT_ID = "test_port_id"
TEST_RESULT = {"id": "clone_vm_id"}
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "tenant_id"


# Create a CloneVMModule object without running its real constructor.
def create_module():
    # Allocate a new module instance while skipping external initialization.
    module = clone_vm.CloneVMModule.__new__(clone_vm.CloneVMModule)
    module.params = {}
    
    module.check_mode = False
    module.conn = mock.Mock()
    
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID
    module.conn.compute = mock.Mock()
    module.conn.network = mock.Mock()
    
    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()
    return module


# Test 1: Verify successful VM cloning by using the source VM ID.
def test_clone_vm_with_id_success():
    module = create_module()
    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "clonevm_name": TEST_CLONE_VM_NAME,
        "network": None,
        "nics": [],
    }
    # Replace the real clone operation with a successful mock.
    clone_vm.clone_vm_ops = mock.Mock(return_value=TEST_RESULT)
    module.run()
    
    assert clone_vm.clone_vm_ops.called
    assert module.exit_json.called


# Test 2: Verify successful VM cloning by using the source VM name.
def test_clone_vm_with_name_success():
    module = create_module()
    
    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "clonevm_name": TEST_CLONE_VM_NAME,
        "network": None,
        "nics": [],
    }
    server = mock.Mock()
    # Assign the fake source VM ID to the mocked server.
    server.id = TEST_VM_ID
    module.conn.compute.find_server = mock.Mock(return_value=server)
    clone_vm.clone_vm_ops = mock.Mock(return_value=TEST_RESULT)
    
    module.run()
    assert module.conn.compute.find_server.called
    assert clone_vm.clone_vm_ops.called
    assert module.exit_json.called


# Test 3: Verify VM cloning with a NIC that identifies a network by name.
def test_clone_vm_with_network_name():
    module = create_module()
    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "clonevm_name": TEST_CLONE_VM_NAME,
        "network": None,
        # Provide one NIC whose network is identified by name.
        "nics": [
            # Define the network name used by the NIC.
            {"net-name": "test_network"}
        ],
    }
    network = mock.Mock()
    # Assign the fake network ID to the mocked network.
    network.id = TEST_NETWORK_ID
    # Configure find_network to return the mocked network.
    module.conn.network.find_network = mock.Mock(return_value=network)
    # Replace the real clone operation with a successful mock.
    clone_vm.clone_vm_ops = mock.Mock(return_value=TEST_RESULT)
    
    module.run()
    assert module.conn.network.find_network.called
    assert clone_vm.clone_vm_ops.called
    assert module.exit_json.called


# Test 4: Verify that the module handles a clone operation exception.
def test_clone_vm_failure():
    module = create_module()
    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "clonevm_name": TEST_CLONE_VM_NAME,
        "network": None,
        "nics": [],
    }
    clone_vm.clone_vm_ops = mock.Mock(side_effect=Exception("clone failed"))
    module.run()
    
    assert clone_vm.clone_vm_ops.called
    assert module.fail_json.called
    
# Test 5: Verify that VM lookup failure is handled when using the VM name.
def test_clone_vm_name_not_found():
    module = create_module()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "clonevm_name": TEST_CLONE_VM_NAME,
        "network": None,
        "nics": [],
    }

    # Configure the VM lookup to raise an exception.
    module.conn.compute.find_server = mock.Mock(
        # Simulate a VM-not-found error.
        side_effect=Exception("vm not found")
    )

    # Verify that module.run raises the expected exception.
    with pytest.raises(Exception, match="vm not found"):
        module.run()

    assert module.conn.compute.find_server.called    
