import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import capture_vm

TEST_VM_ID = "test_vm_id"
TEST_VM_NAME = "test_vm_name"
TEST_IMAGE_NAME = "test_image"
TEST_RESULT = {"image_id": "test_image_id"}
TEST_AUTH_TOKEN = "auth_token"
TEST_TENANT_ID = "tenant_id"


# Create a CaptureVMModule instance without calling its original constructor.
def create_module():
    module = capture_vm.CaptureVMModule.__new__(
        # Pass the class whose instance must be created.
        capture_vm.CaptureVMModule
    )

    # Initialize the module parameters with an empty dictionary.
    module.params = {}
    # Disable Ansible check mode for these unit tests.
    module.check_mode = False

    # Create a mock cloud connection object.
    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN

    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.compute = mock.Mock()

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


# Test 1: Verify that a VM can be captured successfully by using its ID.
def test_capture_vm_with_id_success():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "image_name": TEST_IMAGE_NAME,
    }

    capture_vm.capture_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert capture_vm.capture_ops.called
    assert module.exit_json.called


# Test 2: Verify that a VM can be captured successfully by using its name.
def test_capture_vm_with_name_success():
    module = create_module()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "image_name": TEST_IMAGE_NAME,
    }

    # Create a fake server returned by the compute service.
    server = mock.Mock()
    server.id = TEST_VM_ID

    # Configure VM lookup by name to return the fake server.
    module.conn.compute.find_server = mock.Mock(
        return_value=server
    )

    # Replace the real capture operation with a successful mock response.
    capture_vm.capture_ops = mock.Mock(
        # Return a fake image result without calling PowerVC.
        return_value=TEST_RESULT
    )

    module.run()

    assert module.conn.compute.find_server.called
    assert capture_vm.capture_ops.called
    assert module.exit_json.called


# Test 3: Verify that the module handles an exception from the capture operation.
def test_capture_vm_failure():
    module = create_module()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "image_name": TEST_IMAGE_NAME,
    }

    # Create a fake server so VM lookup completes before capture fails.
    server = mock.Mock()
    server.id = TEST_VM_ID
    module.conn.compute.find_server.return_value = server

    # Configure the capture operation to raise an exception.
    capture_vm.capture_ops = mock.Mock(
        # Raise this exception when capture_ops is called.
        side_effect=Exception("capture failed")
    )

    module.run()

    assert capture_vm.capture_ops.called
    assert module.fail_json.called


# Test 4: Verify the behavior when VM lookup by name raises an exception.
def test_capture_vm_name_not_found():
    module = create_module()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "image_name": TEST_IMAGE_NAME,
    }

    # Configure VM lookup to raise a not-found exception.
    module.conn.compute.find_server = mock.Mock(
        # Raise this exception when find_server is called.
        side_effect=Exception("vm not found")
    )

    with pytest.raises(Exception, match="vm not found"):
        module.run()

    assert module.conn.compute.find_server.called


# Test 5: Verify successful handling when capture_ops returns an empty dictionary.
def test_capture_vm_empty_result():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "image_name": TEST_IMAGE_NAME,
    }

    # Replace the capture operation with a mock that returns an empty result.
    capture_vm.capture_ops = mock.Mock(
        # Return an empty dictionary to test this edge case.
        return_value={}
    )

    module.run()

    assert capture_vm.capture_ops.called
    assert module.exit_json.called
