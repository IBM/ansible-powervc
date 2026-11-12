import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import copy_volume_type


TEST_VOLUME_TYPE_NAME = "volume1"
TEST_VOLUME_TYPE_ID = "voltype-id"
TEST_COPY_VOLUME_TYPE_NAME = "volume1_copy"
TEST_AUTH_TOKEN = "token"
TEST_TENANT_ID = "tenant-id"

TEST_RESULT = {"id": "new-voltype-id"}


# Create a CopyVolumeTypeModule instance without calling its constructor.
def create_module():

    # Create the module object without running the real initialization logic.
    module = copy_volume_type.CopyVolumeTypeModule.__new__(
        copy_volume_type.CopyVolumeTypeModule
    )

    module.params = {}

    module.check_mode = False

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN

    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.exit_json = mock.Mock()

    module.fail_json = mock.Mock()

    return module


# Test 1: Verify copying a volume type by using its name.
def test_copy_volume_type_with_name():

    module = create_module()

    module.params = {

        "name": TEST_VOLUME_TYPE_NAME,
        "id": None,
        "copy_voltype_name": TEST_COPY_VOLUME_TYPE_NAME,
    }

    # Mock the copy operation and return a successful result.
    copy_volume_type.copy_voltype_ops = mock.Mock(
        return_value={"name": TEST_COPY_VOLUME_TYPE_NAME}
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called

    assert module.exit_json.called


# Test 2: Verify copying a volume type by using its ID.
def test_copy_volume_type_with_id():

    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VOLUME_TYPE_ID,
        "copy_voltype_name": TEST_COPY_VOLUME_TYPE_NAME,
    }

    # Mock the copy operation and return a successful result.
    copy_volume_type.copy_voltype_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called
    assert module.exit_json.called


# Test 3: Verify copying a volume type when both name and ID are supplied.
def test_copy_volume_type_with_name_and_id():

    module = create_module()

    module.params = {

        "name": TEST_VOLUME_TYPE_NAME,
        "id": TEST_VOLUME_TYPE_ID,
        "copy_voltype_name": TEST_COPY_VOLUME_TYPE_NAME,
    }

    # Mock the copy operation and return a successful result.
    copy_volume_type.copy_voltype_ops = mock.Mock(
        return_value={"name": TEST_COPY_VOLUME_TYPE_NAME}
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called
    assert module.exit_json.called


# Test 4: Verify that the module handles an empty copy-operation response.
def test_copy_volume_type_empty_result():

    module = create_module()

    module.params = {
        "name": TEST_VOLUME_TYPE_NAME,
        "id": None,
        "copy_voltype_name": TEST_COPY_VOLUME_TYPE_NAME,
    }

    # Mock the copy operation to return an empty dictionary.
    copy_volume_type.copy_voltype_ops = mock.Mock(
        return_value={}
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called
    assert module.exit_json.called


# Test 5: Verify successful copying when a valid copy name is provided.
def test_copy_volume_type_success():

    module = create_module()

    module.params = {
        "name": TEST_VOLUME_TYPE_NAME,
        "id": None,
        "copy_voltype_name": TEST_COPY_VOLUME_TYPE_NAME,
    }

    copy_volume_type.copy_voltype_ops = mock.Mock(
        return_value={"name": TEST_COPY_VOLUME_TYPE_NAME}
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called
    assert module.exit_json.called


# Test 6: Verify failure when the copied volume type name is missing.
def test_copy_volume_type_name_missing():

    module = create_module()

    module.params = {
        "name": TEST_VOLUME_TYPE_NAME,
        "id": None,
        "copy_voltype_name": None,
    }

    # Mock the copy operation to raise a missing-name exception.
    copy_volume_type.copy_voltype_ops = mock.Mock(
        side_effect=Exception("copy_voltype_name is required")
    )

    module.run()

    assert copy_volume_type.copy_voltype_ops.called
    assert module.fail_json.called