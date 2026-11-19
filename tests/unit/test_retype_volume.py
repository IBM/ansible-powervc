import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import retype_volume


TEST_VOL_ID = "test_volume_id"
TEST_VOL_NAME = "test_volume_name"
TEST_TEMPLATE_ID = "test_template_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_RESULT = {"status": "success"}


@pytest.fixture
def module():
    module = mock.Mock()

    module.params = {
        "name": None,
        "id": TEST_VOL_ID,
        "target_template": TEST_TEMPLATE_ID,
        "migration_policy": "never",
    }

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.block_storage.find_volume.return_value.id = TEST_VOL_ID

    module.check_mode = False
    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


@pytest.fixture
def mock_retype_ops(monkeypatch):
    mock_ops = mock.Mock()

    monkeypatch.setattr(
        retype_volume,
        "retype_ops",
        mock_ops,
    )

    return mock_ops


# Test 1: Verifies successful volume retype using volume ID.
def test_run_with_id(module, mock_retype_ops):
    mock_retype_ops.return_value = TEST_RESULT

    retype_volume.RetypeVolModule.run(module)

    expected_data = {
        "os-retype": {
            "new_type": TEST_TEMPLATE_ID,
            "migration_policy": "never",
        }
    }

    mock_retype_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOL_ID,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Test 2: Verifies successful volume retype using volume name.
def test_run_with_name(module, mock_retype_ops):
    module.params["name"] = TEST_VOL_NAME
    module.params["id"] = None
    module.params["migration_policy"] = "generic"

    mock_retype_ops.return_value = TEST_RESULT

    retype_volume.RetypeVolModule.run(module)

    module.conn.block_storage.find_volume.assert_called_once_with(
        TEST_VOL_NAME,
        ignore_missing=False,
    )

    expected_data = {
        "os-retype": {
            "new_type": TEST_TEMPLATE_ID,
            "migration_policy": "generic",
        }
    }

    mock_retype_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOL_ID,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Test 3: Verifies volume retype with on-demand migration policy.
def test_run_with_on_demand_policy(module, mock_retype_ops):
    module.params["migration_policy"] = "on-demand"

    mock_retype_ops.return_value = TEST_RESULT

    retype_volume.RetypeVolModule.run(module)

    expected_data = {
        "os-retype": {
            "new_type": TEST_TEMPLATE_ID,
            "migration_policy": "on-demand",
        }
    }

    mock_retype_ops.assert_called_once_with(
        module,
        module.conn,
        TEST_AUTH_TOKEN,
        TEST_TENANT_ID,
        TEST_VOL_ID,
        expected_data,
    )

    module.exit_json.assert_called_once_with(
        changed=True,
        result=TEST_RESULT,
    )


# Test 4: Verifies retype operation in check mode.
def test_run_check_mode(module, mock_retype_ops):
    module.check_mode = True

    retype_volume.RetypeVolModule.run(module)

    module.exit_json.assert_called_once_with(
        changed=True,
        msg="Retype operation would be executed",
    )

    mock_retype_ops.assert_not_called()


# Test 5: Verifies failure when volume name is not found.
def test_run_volume_not_found(module, mock_retype_ops):
    module.params["name"] = TEST_VOL_NAME
    module.params["id"] = None

    module.conn.block_storage.find_volume.side_effect = Exception(
        "Volume not found"
    )

    with pytest.raises(Exception, match="Volume not found"):
        retype_volume.RetypeVolModule.run(module)

    mock_retype_ops.assert_not_called()

    module.exit_json.assert_not_called()
