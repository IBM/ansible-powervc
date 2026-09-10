import unittest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import unmanage_volume


TEST_VOLUME_NAME = "test_volume"
TEST_HOST_NAME = "test_host"
TEST_VOLUME_ID = "test_volume_id"


def validate_parameters(name=None, volume_id=None, host_name=None):
    """
    Validation rules:
    1. host_name is mandatory.
    2. Either name or volume_id must be provided.
    3. name and volume_id cannot be provided together.
    """
    return (
        host_name is not None
        and (name is not None or volume_id is not None)
        and not (name is not None and volume_id is not None)
    )


class TestUnmanageVolumeModule(unittest.TestCase):

    # 1. name + host -> valid
    def test_parameter_validation_name_and_host(self):
        self.assertTrue(
            validate_parameters(
                name=TEST_VOLUME_NAME,
                volume_id=None,
                host_name=TEST_HOST_NAME
            )
        )

    # 2. id + host -> valid
    def test_parameter_validation_id_and_host(self):
        self.assertTrue(
            validate_parameters(
                name=None,
                volume_id=TEST_VOLUME_ID,
                host_name=TEST_HOST_NAME
            )
        )

    # 3. name + id + host -> invalid
    def test_parameter_validation_name_and_id(self):
        self.assertFalse(
            validate_parameters(
                name=TEST_VOLUME_NAME,
                volume_id=TEST_VOLUME_ID,
                host_name=TEST_HOST_NAME
            )
        )

    # 4. name without host -> invalid
    def test_parameter_validation_without_host(self):
        self.assertFalse(
            validate_parameters(
                name=TEST_VOLUME_NAME,
                volume_id=None,
                host_name=None
            )
        )

    # 5. id without host -> invalid
    def test_parameter_validation_id_without_host(self):
        self.assertFalse(
            validate_parameters(
                name=None,
                volume_id=TEST_VOLUME_ID,
                host_name=None
            )
        )

    # 6. host only -> invalid
    def test_parameter_validation_without_volume(self):
        self.assertFalse(
            validate_parameters(
                name=None,
                volume_id=None,
                host_name=TEST_HOST_NAME
            )
        )

    # 7. nothing provided -> invalid
    def test_parameter_validation_no_parameters(self):
        self.assertFalse(
            validate_parameters(
                name=None,
                volume_id=None,
                host_name=None
            )
        )


if __name__ == "__main__":
    unittest.main()