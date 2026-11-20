import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import resize_vm


TEST_VM_NAME = "test_vm"
TEST_VM_ID = "test_vm_id"
TEST_TEMPLATE_TYPE = "test_compute_template"
TEST_TEMPLATE_ID = "test_template_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "template_type": TEST_TEMPLATE_TYPE,
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.compute.find_flavor.return_value.id = TEST_TEMPLATE_ID
    module.conn.compute.find_server.return_value.id = TEST_VM_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


@pytest.fixture
def mock_resize_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        resize_vm,
        "resize_ops",
        mock_ops,
    )

    return mock_ops


# Test 1: Verifies successful VM resize using VM ID.
def test_run_with_id(module, mock_resize_ops):
    mock_resize_ops.return_value = TEST_RESULT

    resize_vm.ResizeVMModule.run(module)

    module.conn.compute.find_flavor.assert_called_once_with(
        TEST_TEMPLATE_TYPE,
        ignore_missing=False,
    )

    module.conn.compute.find_server.assert_not_called()

    mock_resize_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_TEMPLATE_ID,
        None,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()


# Test 2: Verifies successful VM resize using VM name.
def test_run_with_name(module, mock_resize_ops):
    module.params["name"] = TEST_VM_NAME

    mock_resize_ops.return_value = TEST_RESULT

    resize_vm.ResizeVMModule.run(module)

    module.conn.compute.find_flavor.assert_called_once_with(
        TEST_TEMPLATE_TYPE,
        ignore_missing=False,
    )

    module.conn.compute.find_server.assert_called_once_with(
        TEST_VM_NAME,
        ignore_missing=False,
    )

    mock_resize_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_TEMPLATE_ID,
        TEST_VM_NAME,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()


# Test 3: Verifies failure when resize operation raises an exception.
def test_run_resize_operation_failure(module, mock_resize_ops):
    mock_resize_ops.side_effect = Exception(
        "Resize operation failed"
    )

    resize_vm.ResizeVMModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: Resize operation failed",
        changed=True,
    )

    module.exit_json.assert_not_called()


# Test 4: Verifies exception when compute template is not found.
def test_run_template_not_found(module, mock_resize_ops):
    module.conn.compute.find_flavor.side_effect = Exception(
        "Template not found"
    )

    with pytest.raises(Exception, match="Template not found"):
        resize_vm.ResizeVMModule.run(module)

    mock_resize_ops.assert_not_called()

    module.exit_json.assert_not_called()


# Test 5: Verifies exception when VM name is not found.
def test_run_vm_not_found(module, mock_resize_ops):
    module.params["name"] = TEST_VM_NAME

    module.conn.compute.find_server.side_effect = Exception(
        "VM not found"
    )

    with pytest.raises(Exception, match="VM not found"):
        resize_vm.ResizeVMModule.run(module)

    mock_resize_ops.assert_not_called()

    module.exit_json.assert_not_called()
