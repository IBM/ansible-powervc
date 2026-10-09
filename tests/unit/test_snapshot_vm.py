import pytest
import unittest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import snapshot_vm


TEST_VM_NAME = "test_vm"
TEST_VM_ID = "vm-id"

TEST_SNAPSHOT_NAME = "snapshot1"
TEST_SNAPSHOT_DESCRIPTION = "test snapshot"


def create_module(volume):

    obj = snapshot_vm.SnapshotVMModule.__new__(
        snapshot_vm.SnapshotVMModule
    )

    obj.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "snapshot_name": TEST_SNAPSHOT_NAME,
        "snapshot_description": TEST_SNAPSHOT_DESCRIPTION,
        "volume": volume
    }

    obj.conn = mock.Mock()

    obj.conn.auth_token = "token"
    obj.conn.session.get_project_id.return_value = "tenant-id"

    server = mock.Mock()
    server.id = TEST_VM_ID

    obj.conn.compute.find_server.return_value = server

    obj.exit_json = mock.Mock()
    obj.fail_json = mock.Mock()

    return obj


# ---------------------------------------------------------
# Test 1 : All Volume Snapshot
# ---------------------------------------------------------

def test_all_volume_snapshot():

    module = create_module(
        {
            "type": "All"
        }
    )

    snapshot_vm.snapshot_ops = mock.Mock(
        return_value={"snapshot": TEST_SNAPSHOT_NAME}
    )

    module.run()

    module.exit_json.assert_called_once()


# ---------------------------------------------------------
# Test 2 : Boot Volume Snapshot
# ---------------------------------------------------------

def test_boot_volume_snapshot():

    module = create_module(
        {
            "type": "Boot"
        }
    )

    snapshot_vm.snapshot_ops = mock.Mock(
        return_value={"snapshot": TEST_SNAPSHOT_NAME}
    )

    module.run()

    module.exit_json.assert_called_once()


# ---------------------------------------------------------
# Test 3 : Specific Volume Snapshot
# ---------------------------------------------------------

def test_specific_volume_snapshot():

    module = create_module(
        {
            "type": "Specific",
            "name": ["volume1"]
        }
    )

    snapshot_vm.snapshot_ops = mock.Mock(
        return_value={"snapshot": TEST_SNAPSHOT_NAME}
    )

    module.run()

    module.exit_json.assert_called_once()


# ---------------------------------------------------------
# Test 4 : Snapshot Failure
# ---------------------------------------------------------

def test_snapshot_failure():

    module = create_module(
        {
            "type": "All"
        }
    )

    snapshot_vm.snapshot_ops = mock.Mock(
        side_effect=Exception("snapshot failed")
    )

    module.run()

    module.fail_json.assert_called_once()


# ---------------------------------------------------------
# Test 5 : Verify VM Lookup By Name
# ---------------------------------------------------------

def test_snapshot_find_vm_by_name():

    module = create_module(
        {
            "type": "All"
        }
    )

    snapshot_vm.snapshot_ops = mock.Mock(
        return_value={"snapshot": TEST_SNAPSHOT_NAME}
    )

    module.run()

    module.conn.compute.find_server.assert_called_once_with(
        TEST_VM_NAME,
        ignore_missing=False
    )