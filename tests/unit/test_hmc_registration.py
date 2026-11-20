
import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import hmc_registration


TEST_HOST_ID = "test_host_id"
TEST_HOST_NAME = "test_hmc"
TEST_ACCESS_IP = "192.168.1.100"
TEST_USER = "test_user"
TEST_PASSWORD = "test_password"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


# Creates a mocked module with test parameters and connection details.
@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "host_id": TEST_HOST_ID,
        "user": TEST_USER,
        "access_ip": TEST_ACCESS_IP,
        "name": TEST_HOST_NAME,
        "password": TEST_PASSWORD,
        "state": "present",
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


# Replaces host_ops with a mock to prevent real API calls.
@pytest.fixture
def mock_host_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        hmc_registration,
        "host_ops",
        mock_ops,
    )

    return mock_ops


# Verifies successful HMC registration using state present.
def test_run_with_present_state(module, mock_host_ops):
    mock_host_ops.return_value = TEST_RESULT

    hmc_registration.HostAddModule.run(module)

    expected_data = {
        "hmc": {
            "registration": {
                "access_ip": TEST_ACCESS_IP,
                "user_id": TEST_USER,
                "hmc_display_name": TEST_HOST_NAME,
                "password": TEST_PASSWORD,
                "auto_add_certificate": True,
            }
        }
    }

    mock_host_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "present",
        TEST_HOST_ID,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        changed=False,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()


# Verifies successful HMC unregistration using state absent.
def test_run_with_absent_state(module, mock_host_ops):
    module.params["state"] = "absent"
    mock_host_ops.return_value = TEST_RESULT

    hmc_registration.HostAddModule.run(module)

    mock_host_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        "absent",
        TEST_HOST_ID,
        None,
    )

    module.exit_json.assert_called_once_with(
        changed=False,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()

# Verifies that registration failure is handled when access IP is missing.
def test_run_registration_missing_access_ip(module, mock_host_ops):
    module.params["access_ip"] = None

    mock_host_ops.side_effect = Exception(
        "access_ip is required"
    )

    hmc_registration.HostAddModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: access_ip is required",
        changed=False,
    )

    module.exit_json.assert_not_called()