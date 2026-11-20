import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import manage_vm


TEST_VM_NAME = "test_vm"
TEST_VM_ID = "test_vm_id"
TEST_HOST = "test_host"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


# Create a mocked module with test parameters and connection details.
@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "host": TEST_HOST,
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN

    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID
    module.conn.compute = mock.Mock()

    return module


# Replaces manage_ops with a mock to prevent real API calls.
@pytest.fixture
def mock_manage_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        manage_vm,
        "manage_ops",
        mock_ops,
    )

    return mock_ops


# Verifies that a VM is managed successfully using its name.
def test_run_with_name(module, mock_manage_ops):
    vm = mock.Mock()
    vm.id = TEST_VM_ID

    module.params["name"] = TEST_VM_NAME
    module.params["id"] = None
    module.params["host"] = TEST_HOST

    module.conn.compute.find_server.return_value = vm
    mock_manage_ops.return_value = TEST_RESULT

    manage_vm.ManageVMModule.run(module)

    module.conn.compute.find_server.assert_called_once_with(
        TEST_VM_NAME,
        ignore_missing=False,
    )

    mock_manage_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_HOST,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Verifies that a VM is managed successfully using its ID.
def test_run_with_id(module, mock_manage_ops):
    module.params["name"] = None
    module.params["id"] = TEST_VM_ID
    module.params["host"] = TEST_HOST

    mock_manage_ops.return_value = TEST_RESULT

    manage_vm.ManageVMModule.run(module)

    mock_manage_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_HOST,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Verifies that fail_json is called when manage_ops raises an exception.
def test_run_manage_operation_failure(module, mock_manage_ops):

    module.params["name"] = None
    module.params["id"] = TEST_VM_ID
    module.params["host"] = TEST_HOST

    mock_manage_ops.side_effect = Exception("Manage operation failed")

    manage_vm.ManageVMModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: Manage operation failed",
        changed=True,
    )

    module.exit_json.assert_not_called()


# Verifies that an exception is raised when the VM name is not found.
def test_run_name_not_found(module, mock_manage_ops):

    module.params["name"] = TEST_VM_NAME
    module.params["id"] = None
    module.params["host"] = TEST_HOST

    module.conn.compute.find_server.side_effect = Exception(
        "VM not found"
    )

    with pytest.raises(Exception, match="VM not found"):
        manage_vm.ManageVMModule.run(module)

    mock_manage_ops.assert_not_called()
