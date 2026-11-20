import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import host_maintenance


TEST_HOST = "test_host"
TEST_STATUS = "enable"
TEST_MIGRATE = "all"
TEST_TARGET_HOST = "target_host"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "host": TEST_HOST,
        "status": TEST_STATUS,
        "migrate": TEST_MIGRATE,
        "target_host": TEST_TARGET_HOST,
    }

    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


@pytest.fixture
def mock_maintenance_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        host_maintenance,
        "maintenance_ops",
        mock_ops,
    )

    return mock_ops


# Test 1: Verifies successful host maintenance execution.
def test_run_success(module, mock_maintenance_ops):
    mock_maintenance_ops.return_value = TEST_RESULT

    host_maintenance.HostMaintenanceModule.run(module)

    mock_maintenance_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_HOST,
        TEST_STATUS,
        TEST_MIGRATE,
        TEST_TARGET_HOST,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Test 2: Verifies failure when the required host parameter is missing.
def test_run_missing_host(module, mock_maintenance_ops):
    module.params["host"] = None

    host_maintenance.HostMaintenanceModule.run(module)

    mock_maintenance_ops.assert_called_once()


# Test 3: Verifies failure when the required status parameter is missing.
def test_run_missing_status(module, mock_maintenance_ops):
    module.params["status"] = None

    host_maintenance.HostMaintenanceModule.run(module)

    mock_maintenance_ops.assert_called_once()


# Test 4: Verifies that an error is handled when maintenance fails.
def test_run_failure(module, mock_maintenance_ops):
    mock_maintenance_ops.side_effect = Exception(
        "Maintenance operation failed"
    )

    host_maintenance.HostMaintenanceModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: Maintenance operation failed",
        changed=True,
    )

    module.exit_json.assert_not_called()
