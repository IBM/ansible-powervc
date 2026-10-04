import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import group_action


TEST_GROUP_ID = "test_group_id"
TEST_ACTION_SHOW = "show"
TEST_ACTION_RELATIONSHIP = "relationship"
TEST_ACTION_START = "start"
TEST_ACTION_STOP = "stop"
TEST_PRIMARY_MASTER = "master"
TEST_PRIMARY_AUX = "aux"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"


def create_module():
    module = group_action.GroupActionModule.__new__(
        group_action.GroupActionModule
    )

    module.params = {}
    module.check_mode = False

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN

    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.block_storage = mock.Mock()
    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module

#Test 1: Verifies that the show action retrieves and displays group details
def test_group_action_show_success():
    module = create_module()

    module.params = {
        "id": TEST_GROUP_ID,
        "action": TEST_ACTION_SHOW,
        "secondary": False,
        "primary": None,
        "access": False,
    }

    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    group_action.group_action = mock.Mock(
        return_value=(
            {"id": TEST_GROUP_ID},
            False,
        )
    )

    module.run()

    assert module.conn.block_storage.get_group.called
    assert group_action.group_action.called
    assert module.exit_json.called

#Test 2: Verifies that the relationship action completes successfully for a secondary
def test_group_action_relationship_success():
    module = create_module()

    module.params = {
        "id": TEST_GROUP_ID,
        "action": TEST_ACTION_RELATIONSHIP,
        "secondary": True,
        "primary": None,
        "access": False,
    }

    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    group_action.group_action = mock.Mock(
        return_value=(
            {"id": TEST_GROUP_ID},
            False,
        )
    )

    module.run()

    assert module.conn.block_storage.get_group.called
    assert group_action.group_action.called
    assert module.exit_json.called

#Test 3: Verifies that the start action completes successfully when master is provided
def test_group_action_start_master_success():
    module = create_module()

    module.params = {
        "id": TEST_GROUP_ID,
        "action": TEST_ACTION_START,
        "secondary": False,
        "primary": TEST_PRIMARY_MASTER,
        "access": False,
    }

    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    group_action.group_action = mock.Mock(
        return_value=(
            {"id": TEST_GROUP_ID},
            False,
        )
    )

    module.run()

    assert module.conn.block_storage.get_group.called
    assert group_action.group_action.called
    assert module.exit_json.called

#Test 4: Verifies that the start action fails when the required primary value is not
def test_group_action_start_without_primary():
    module = create_module()

    module.params = {
        "id": TEST_GROUP_ID,
        "action": TEST_ACTION_START,
        "secondary": False,
        "primary": None,
        "access": False,
    }

    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    module.fail_json = mock.Mock(
        side_effect=Exception("primary is required")
    )

    with pytest.raises(Exception, match="primary is required"):
        module.run()

    assert module.conn.block_storage.get_group.called
    assert module.fail_json.called

#Test 5: Verifies that the stop action completes successfully when access is enabled    
def test_group_action_start_with_access_success():
    module = create_module()

    module.params = {
        "id": TEST_GROUP_ID,
        "action": TEST_ACTION_STOP,
        "secondary": False,
        "primary": None,
        "access": True,
    }

    module.conn.block_storage.get_group = mock.Mock(
        return_value={"id": TEST_GROUP_ID}
    )

    group_action.group_action = mock.Mock(
        return_value=(
            {"id": TEST_GROUP_ID},
            True,
        )
    )

    module.run()

    assert module.conn.block_storage.get_group.called
    assert group_action.group_action.called
    assert module.exit_json.called    