
import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import novalink


TEST_HOST_ID = "test_host_id"
TEST_HOST_NAME = "test_host_name"
TEST_ACCESS_IP = "test_access_ip"
TEST_USER = "test_user"
TEST_PASSWORD = "test_password"
TEST_SSH_KEY = "test_private_key"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "id": None,
        "user": TEST_USER,
        "name": TEST_HOST_NAME,
        "host": TEST_ACCESS_IP,
        "password": TEST_PASSWORD,
        "ssh_key": TEST_SSH_KEY,
        "host_group": "Default_Group",
        "stand_by": False,
        "standby_tag": "unplanned_maintenance",
        "force": False,
        "state": "present",
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN

    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


@pytest.fixture
def mock_host_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        novalink,
        "host_ops",
        mock_ops,
    )

    return mock_ops


# TEST 1: Verifies successful Novalink registration
def test_run_with_present_state(module, mock_host_ops):
    mock_host_ops.return_value = TEST_RESULT

    novalink.HostAddModule.run(module)

    expected_data = {
        "host": {
            "registration": {
                "access_ip": TEST_ACCESS_IP,
                "user_id": TEST_USER,
                "host_type": "powervm",
                "asynchronous": True,
                "host_standby": False,
                "host_group": "Default_Group",
                "host_display_name": TEST_HOST_NAME,
                "password": TEST_PASSWORD,
                "private_key_data": TEST_SSH_KEY,
                "force_unmanage": False,
                "auto_add_host_key": True,
                "force_switch": False,
            }
        }
    }

    mock_host_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "present",
        None,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        **TEST_RESULT
    )

    module.fail_json.assert_not_called()


# TEST 2: Verifies successful Novalink unregistration
def test_run_with_absent_state(module, mock_host_ops):
    module.params["state"] = "absent"
    module.params["id"] = "test_host_id"

    mock_host_ops.return_value = TEST_RESULT

    novalink.HostAddModule.run(module)

    mock_host_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "absent",
        "test_host_id",
        None,
    )

    module.exit_json.assert_called_once_with(
        **TEST_RESULT
    )

    module.fail_json.assert_not_called()


# TEST 3: Verifies Novalink registration with standby enabled
def test_run_with_standby_enabled(module, mock_host_ops):
    module.params["stand_by"] = True
    module.params["standby_tag"] = "unplanned_maintenance"

    mock_host_ops.return_value = TEST_RESULT

    novalink.HostAddModule.run(module)

    expected_data = {
        "host": {
            "registration": {
                "access_ip": TEST_ACCESS_IP,
                "user_id": TEST_USER,
                "host_type": "powervm",
                "asynchronous": True,
                "host_standby": True,
                "host_group": "Default_Group",
                "host_display_name": TEST_HOST_NAME,
                "password": TEST_PASSWORD,
                "private_key_data": TEST_SSH_KEY,
                "force_unmanage": False,
                "auto_add_host_key": True,
                "force_switch": False,
                "standby_tag": "unplanned_maintenance",
            }
        }
    }

    mock_host_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "present",
        None,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        **TEST_RESULT
    )

    module.fail_json.assert_not_called()
