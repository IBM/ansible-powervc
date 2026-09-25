#!/usr/bin/python

import unittest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import unmanage_volume


TEST_VOLUME_NAME = "test_volume"
TEST_HOST_NAME = "test_host"
TEST_VOLUME_ID = "test_volume_id"
TEST_RESOLVED_VOLUME_ID = "resolved_volume_id"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"


class TestUnmanageVolumeModule(unittest.TestCase):

    @mock.patch.object(unmanage_volume, "unmanage_ops")
    def test_run_with_volume_id(self, mock_unmanage_ops):
        module = mock.Mock()

        module.conn.auth_token = TEST_AUTH_TOKEN
        module.conn.session.get_project_id.return_value = TEST_TENANT_ID

        module.params = {
            "name": None,
            "id": TEST_VOLUME_ID,
            "host_name": TEST_HOST_NAME,
        }

        mock_unmanage_ops.return_value = {
            "status": "success",
        }

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

        module.exit_json.assert_called_once_with(
            changed=True,
            result={"status": "success"},
        )

    @mock.patch.object(unmanage_volume, "unmanage_ops")
    def test_run_with_volume_name(self, mock_unmanage_ops):
        module = mock.Mock()

        module.conn.auth_token = TEST_AUTH_TOKEN
        module.conn.session.get_project_id.return_value = TEST_TENANT_ID

        module.params = {
            "name": TEST_VOLUME_NAME,
            "id": None,
            "host_name": TEST_HOST_NAME,
        }

        volume = mock.Mock()
        volume.id = TEST_RESOLVED_VOLUME_ID

        module.conn.block_storage.find_volume.return_value = volume

        mock_unmanage_ops.return_value = {
            "status": "success",
        }

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
            TEST_RESOLVED_VOLUME_ID,
            TEST_HOST_NAME,
        )

        module.exit_json.assert_called_once_with(
            changed=True,
            result={"status": "success"},
        )

    @mock.patch.object(unmanage_volume, "unmanage_ops")
    def test_run_unmanage_operation_failure(self, mock_unmanage_ops):
        module = mock.Mock()

        module.conn.auth_token = TEST_AUTH_TOKEN
        module.conn.session.get_project_id.return_value = TEST_TENANT_ID

        module.params = {
            "name": None,
            "id": TEST_VOLUME_ID,
            "host_name": TEST_HOST_NAME,
        }

        mock_unmanage_ops.side_effect = Exception(
            "Unmanage operation failed"
        )

        unmanage_volume.UnmanageVolModule.run(module)

        module.fail_json.assert_called_once_with(
            msg="An unexpected error occurred: Unmanage operation failed",
            changed=True,
        )

        module.exit_json.assert_not_called()

    @mock.patch.object(unmanage_volume, "unmanage_ops")
    def test_run_passes_host_name(self, mock_unmanage_ops):
        module = mock.Mock()

        module.conn.auth_token = TEST_AUTH_TOKEN
        module.conn.session.get_project_id.return_value = TEST_TENANT_ID

        module.params = {
            "name": None,
            "id": TEST_VOLUME_ID,
            "host_name": TEST_HOST_NAME,
        }

        mock_unmanage_ops.return_value = {
            "status": "success",
        }

        unmanage_volume.UnmanageVolModule.run(module)

        mock_unmanage_ops.assert_called_once_with(
            module,
            module.conn,
            TEST_AUTH_TOKEN,
            TEST_TENANT_ID,
            TEST_VOLUME_ID,
            TEST_HOST_NAME,
        )

    @mock.patch.object(unmanage_volume, "unmanage_ops")
    def test_run_gets_project_id(self, mock_unmanage_ops):
        module = mock.Mock()

        module.conn.auth_token = TEST_AUTH_TOKEN
        module.conn.session.get_project_id.return_value = TEST_TENANT_ID

        module.params = {
            "name": None,
            "id": TEST_VOLUME_ID,
            "host_name": TEST_HOST_NAME,
        }

        mock_unmanage_ops.return_value = {
            "status": "success",
        }

        unmanage_volume.UnmanageVolModule.run(module)

        module.conn.session.get_project_id.assert_called_once_with()

        mock_unmanage_ops.assert_called_once_with(
            module,
            module.conn,
            TEST_AUTH_TOKEN,
            TEST_TENANT_ID,
            TEST_VOLUME_ID,
            TEST_HOST_NAME,
        )


if __name__ == "__main__":
    unittest.main()
