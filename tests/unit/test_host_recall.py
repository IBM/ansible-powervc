import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import host_recall

TEST_HOST = "test_host_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


# Creates a mocked module with test parameters and connection details.
@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "host": TEST_HOST,
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


# Replaces recall_ops with a mock to prevent real API calls.
@pytest.fixture
def mock_recall_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        host_recall,
        "recall_ops",
        mock_ops,
    )

    return mock_ops


# Verifies that virtual machines are recalled successfully.
def test_run_success(module, mock_recall_ops):
    mock_recall_ops.return_value = TEST_RESULT

    host_recall.HostRecallModule.run(module)

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )

    module.fail_json.assert_not_called()


# Verifies that the correct connection details and host are passed.
def test_run_passes_correct_parameters(module, mock_recall_ops):
    mock_recall_ops.return_value = TEST_RESULT

    host_recall.HostRecallModule.run(module)

    mock_recall_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_HOST,
    )


# Verifies that the host parameter is passed correctly.
def test_run_with_host(module, mock_recall_ops):
    module.params["host"] = TEST_HOST
    mock_recall_ops.return_value = TEST_RESULT

    host_recall.HostRecallModule.run(module)

    assert module.params["host"] == TEST_HOST

    mock_recall_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_HOST,
    )


# Verifies that an exception from recall_ops is handled correctly.
def test_run_recall_failure(module, mock_recall_ops):
    mock_recall_ops.side_effect = Exception("Recall operation failed")

    host_recall.HostRecallModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: Recall operation failed",
        changed=True,
    )

    module.exit_json.assert_not_called()


# Verifies that the authentication token and tenant ID are retrieved.
def test_run_connection_details(module, mock_recall_ops):
    mock_recall_ops.return_value = TEST_RESULT

    host_recall.HostRecallModule.run(module)

    module.conn.session.get_project_id.assert_called_once_with()

    mock_recall_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_HOST,
    )
