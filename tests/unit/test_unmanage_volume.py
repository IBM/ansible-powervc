import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import unmanage_volume

TEST_VOLUME_NAME = "test_volume"
TEST_HOST_NAME = "test_host"
TEST_VOLUME_ID = "test_volume_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"


# Creates a mocked module with test parameters and connection details.
@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "name": TEST_VOLUME_NAME,
        "id": None,
        "host_name": TEST_HOST_NAME,
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID
    module.conn.block_storage = mock.Mock()

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


# Replaces unmanage_ops with a mock to prevent real API calls.
@pytest.fixture
def mock_unmanage_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        unmanage_volume,
        "unmanage_ops",
        mock_ops,
    )

    return mock_ops


# Verifies that a volume is unmanaged successfully using its name.
def test_run_with_name(module, mock_unmanage_ops):
    volume = mock.Mock()
    volume.id = TEST_VOLUME_ID

    module.params["name"] = TEST_VOLUME_NAME
    module.params["id"] = None
    module.params["host_name"] = TEST_HOST_NAME

    module.conn.block_storage.find_volume.return_value = volume
    mock_unmanage_ops.return_value = {"status": "success"}

    unmanage_volume.UnmanageVolModule.run(module)

    module.conn.block_storage.find_volume.assert_called_once_with(
        TEST_VOLUME_NAME,
        ignore_missing=False,
    )

    mock_unmanage_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOLUME_ID,
        TEST_HOST_NAME,
    )


# Verifies that a volume is unmanaged successfully using its ID.
def test_run_with_id(module, mock_unmanage_ops):
    module.params["name"] = None
    module.params["id"] = TEST_VOLUME_ID
    module.params["host_name"] = TEST_HOST_NAME

    mock_unmanage_ops.return_value = {"status": "success"}

    unmanage_volume.UnmanageVolModule.run(module)

    module.conn.block_storage.find_volume.assert_not_called()

    mock_unmanage_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOLUME_ID,
        TEST_HOST_NAME,
    )


# Verifies that the operation fails when only the host name is provided.
def test_run_with_only_host_name(module, mock_unmanage_ops):
    module.params["name"] = None
    module.params["id"] = None
    module.params["host_name"] = TEST_HOST_NAME

    mock_unmanage_ops.side_effect = Exception(
        "volume ID is required"
    )

    unmanage_volume.UnmanageVolModule.run(module)

    module.fail_json.assert_called_once_with(
        msg="An unexpected error occurred: volume ID is required",
        changed=True,
    )


# Verifies that the operation fails when the volume name is not found.
def test_run_name_not_found(module, mock_unmanage_ops):
    module.params["name"] = TEST_VOLUME_NAME
    module.params["id"] = None
    module.params["host_name"] = TEST_HOST_NAME

    module.conn.block_storage.find_volume.side_effect = Exception(
        "Volume not found"
    )

    with pytest.raises(Exception, match="Volume not found"):
        unmanage_volume.UnmanageVolModule.run(module)

    mock_unmanage_ops.assert_not_called()


# Verifies that the provided host name is passed correctly to unmanage_ops.
def test_run_passes_host_name(module, mock_unmanage_ops):
    module.params["name"] = TEST_VOLUME_NAME
    module.params["id"] = None
    module.params["host_name"] = TEST_HOST_NAME

    volume = mock.Mock()
    volume.id = TEST_VOLUME_ID

    module.conn.block_storage.find_volume.return_value = volume
    mock_unmanage_ops.return_value = {"status": "success"}

    unmanage_volume.UnmanageVolModule.run(module)

    mock_unmanage_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOLUME_ID,
        TEST_HOST_NAME,
    )    