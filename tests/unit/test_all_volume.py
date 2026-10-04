from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import all_volumes


TEST_HOST_METADATA_NAME = "host1"


def create_module():

    obj = all_volumes.AllVolumeInfoModule.__new__(
        all_volumes.AllVolumeInfoModule
    )

    obj.params = {
        "host_metadata_name": TEST_HOST_METADATA_NAME
    }

    obj.conn = mock.Mock()

    obj.conn.auth_token = "token"
    obj.conn.session.get_project_id.return_value = "tenant-id"

    obj.exit_json = mock.Mock()
    obj.fail_json = mock.Mock()

    return obj


# ---------------------------------------------------------
# Test 1 : All Volumes Success
# ---------------------------------------------------------

def test_all_volumes_success():

    module = create_module()

    all_volumes.volume_ops = mock.Mock(
        return_value={
            "volumes": [
                {
                    "id": "vol-id",
                    "name": "volume1"
                }
            ]
        }
    )

    module.run()

    module.exit_json.assert_called_once()


# ---------------------------------------------------------
# Test 2 : All Volumes Failure
# ---------------------------------------------------------

def test_all_volumes_failure():

    module = create_module()

    all_volumes.volume_ops = mock.Mock(
        side_effect=Exception("volume fetch failed")
    )

    module.run()

    module.fail_json.assert_called_once()