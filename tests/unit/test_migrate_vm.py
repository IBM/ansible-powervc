import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import migrate_vm


TEST_VM_ID = "test_vm_id"
TEST_VM_NAME = "test_vm_name"
TEST_HOST = "test_host"
TEST_RESULT = {"status": "success"}
TEST_AUTH_TOKEN = "auth_token"
TEST_TENANT_ID = "tenant_id"


def create_module():
    module = migrate_vm.MigrateVMModule.__new__(
        migrate_vm.MigrateVMModule
    )

    module.params = {}
    module.check_mode = False

    module.conn = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID

    module.conn.session.verify = True

    module.conn.compute = mock.Mock()

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


def test_live_migration_with_id():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "host": TEST_HOST,
        "type": "live",
        "ignore_az": False,
        "block_migration": False,
        "disk_over_commit": True,
        "force": False,
        "validate_certs": True,
    }

    migrate_vm.migrate_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert migrate_vm.migrate_ops.called


def test_live_migration_with_name():
    module = create_module()

    module.params = {
        "name": TEST_VM_NAME,
        "id": None,
        "host": TEST_HOST,
        "type": "live",
        "ignore_az": False,
        "block_migration": False,
        "disk_over_commit": True,
        "force": False,
        "validate_certs": True,
    }

    server = mock.Mock()
    server.id = TEST_VM_ID

    module.conn.compute.find_server.return_value = server

    migrate_vm.migrate_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert module.conn.compute.find_server.called
    assert migrate_vm.migrate_ops.called
    assert module.exit_json.called


def test_cold_migration():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "host": TEST_HOST,
        "type": "cold",
        "ignore_az": False,
        "block_migration": False,
        "disk_over_commit": True,
        "force": False,
        "validate_certs": True,
    }

    migrate_vm.migrate_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert migrate_vm.migrate_ops.called
    assert module.exit_json.called


def test_empty_result():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "host": None,
        "type": "live",
        "ignore_az": False,
        "block_migration": False,
        "disk_over_commit": True,
        "force": False,
        "validate_certs": True,
    }

    migrate_vm.migrate_ops = mock.Mock(
        return_value={}
    )

    module.run()

    assert migrate_vm.migrate_ops.called
    assert module.exit_json.called


def test_validate_certs_false():
    module = create_module()

    module.params = {
        "name": None,
        "id": TEST_VM_ID,
        "host": TEST_HOST,
        "type": "live",
        "ignore_az": False,
        "block_migration": False,
        "disk_over_commit": True,
        "force": False,
        "validate_certs": False,
    }

    migrate_vm.migrate_ops = mock.Mock(
        return_value=TEST_RESULT
    )

    module.run()

    assert module.conn.session.verify is False
    assert module.exit_json.called
