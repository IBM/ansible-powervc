import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import pin_vm


TEST_VM_NAME = "test_vm"
TEST_VM_ID = "test_vm_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_PIN_TYPE = "soft_pin"
TEST_RESULT = {"status": "success"}


@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "pin_type": TEST_PIN_TYPE,
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.compute.find_server.return_value.id = TEST_VM_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


@pytest.fixture
def mock_pin_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        pin_vm,
        "pin_ops",
        mock_ops,
    )

    return mock_ops


def test_vm_success(module, mock_pin_ops):
    mock_pin_ops.return_value = TEST_RESULT

    pin_vm.PinOpsModule.run(module)

    module.exit_json.assert_called_once_with(
        changed=False,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()


def test_run_passes_correct_parameters(module, mock_pin_ops):
    mock_pin_ops.return_value = TEST_RESULT

    pin_vm.PinOpsModule.run(module)

    mock_pin_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_PIN_TYPE,
    )


def test_run_with_vm_name(module, mock_pin_ops):
    module.params["name"] = TEST_VM_NAME
    mock_pin_ops.return_value = TEST_RESULT

    pin_vm.PinOpsModule.run(module)

    module.conn.compute.find_server.assert_called_once_with(
        TEST_VM_NAME,
        ignore_missing=False,
    )

    mock_pin_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        TEST_PIN_TYPE,
    )


def test_run_with_invalid_vm_id(module, mock_pin_ops):
    module.params["id"] = "invalid_vm_id"
    mock_pin_ops.return_value = TEST_RESULT

    pin_vm.PinOpsModule.run(module)

    mock_pin_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "invalid_vm_id",
        TEST_PIN_TYPE,
    )

    module.exit_json.assert_called_once_with(
        changed=False,
        result=TEST_RESULT,
    )


@pytest.mark.parametrize(
    "pin_type",
    ["no_pin", "soft_pin", "hard_pin"],
)
def test_run_valid_pin_types(module, mock_pin_ops, pin_type):
    module.params["pin_type"] = pin_type
    mock_pin_ops.return_value = TEST_RESULT

    pin_vm.PinOpsModule.run(module)

    mock_pin_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VM_ID,
        pin_type,
    )

    module.exit_json.assert_called_once_with(
        changed=False,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()
