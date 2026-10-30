import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import fabric


TEST_FABRIC_ID = "test-fabric-id"
TEST_HOST = "test-host"
TEST_USER = "test-user"
TEST_PASSWORD = "test-password"
TEST_FABRIC_NAME = "test-fabric"
TEST_TYPE = "test-type"
TEST_ZONING_POLICY = "test-zoning-policy"
TEST_AUTH_TOKEN = "test-auth-token"
TEST_TENANT_ID = "test-tenant-id"
TEST_ENDPOINT = "https://test-endpoint"
TEST_VSAN = "test-vsan"
TEST_PORT = "22"
TEST_SSH_KEY = "test-ssh-key"
TEST_VIRTUAL_FABRIC_ID = "test-virtual-fabric-id"
TEST_CISCO_NAME = "test-cisco-name"


def create_module():
    module = fabric.FabricModule.__new__(fabric.FabricModule)
    module.params = {}
    module.check_mode = False
    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID
    module.conn.session.verify = True
    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module

# Test 1: Verify successful Cisco registration using a password. 
def test_cisco_register_with_password():
    module = create_module()

    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST,
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "ssh_key": None,
        "name": TEST_FABRIC_NAME,
        "type": "cisco",
        "zoning_policy": TEST_ZONING_POLICY,
        "auto_add_host_key": True,
        "virtual_fabric_id": None,
        "port": TEST_PORT,
        "vsan": TEST_VSAN,
    }

    fabric.get_endpoint_url_by_service_name = mock.Mock(
        return_value=TEST_ENDPOINT
    )

    fabric.fabric_ops = mock.Mock(
        return_value={"id": TEST_FABRIC_ID}
    )

    module.run()

    assert fabric.get_endpoint_url_by_service_name.called
    assert fabric.fabric_ops.called
    assert module.exit_json.called

# Test 2: Verify successful Cisco registration using an SSH key.
def test_cisco_register_with_ssh_key():
    module = create_module()

    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST,
        "user": TEST_USER,
        "password": None,
        "ssh_key": TEST_SSH_KEY,
        "name": TEST_FABRIC_NAME,
        "type": "cisco",
        "zoning_policy": TEST_ZONING_POLICY,
        "auto_add_host_key": True,
        "virtual_fabric_id": None,
        "port": TEST_PORT,
        "vsan": TEST_VSAN,
    }

    fabric.get_endpoint_url_by_service_name = mock.Mock(
        return_value=TEST_ENDPOINT
    )

    fabric.fabric_ops = mock.Mock(
        return_value={"id": TEST_FABRIC_ID}
    )

    module.run()

    assert fabric.get_endpoint_url_by_service_name.called
    assert fabric.fabric_ops.called
    assert module.exit_json.called

# Test 3: Verify Cisco registration failure when VSAN is missing.
def test_cisco_register_without_vsan():
    module = create_module()

    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST,
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "ssh_key": None,
        "name": TEST_FABRIC_NAME,
        "type": "cisco",
        "zoning_policy": TEST_ZONING_POLICY,
        "auto_add_host_key": True,
        "virtual_fabric_id": None,
        "port": TEST_PORT,
        "vsan": None,
    }

    fabric.get_endpoint_url_by_service_name = mock.Mock(
        return_value=TEST_ENDPOINT
    )

    fabric.fabric_ops = mock.Mock(
        side_effect=Exception("VSAN is required")
    )

    with pytest.raises(Exception, match="VSAN is required"):
        module.run()

    assert fabric.get_endpoint_url_by_service_name.called
    assert fabric.fabric_ops.called

# Test 4: Verify successful Brocade fabric registration using a password.
def test_brocade_register_with_password():
    module = create_module()

    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST,
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "ssh_key": None,
        "name": TEST_FABRIC_NAME,
        "type": "brocade",
        "zoning_policy": TEST_ZONING_POLICY,
        "auto_add_host_key": True,
        "virtual_fabric_id": TEST_VIRTUAL_FABRIC_ID,
        "port": TEST_PORT,
        "vsan": None,
    }

    fabric.get_endpoint_url_by_service_name = mock.Mock(
        return_value=TEST_ENDPOINT
    )

    fabric.fabric_ops = mock.Mock(
        return_value={"id": TEST_FABRIC_ID}
    )

    module.run()

    assert fabric.get_endpoint_url_by_service_name.called
    assert fabric.fabric_ops.called
    assert module.exit_json.called

# Test 5: Verify registration failure when fabric_ops raises an exception.
def test_fabric_register_failure():
    module = create_module()

    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST,
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "ssh_key": None,
        "name": TEST_FABRIC_NAME,
        "type": "brocade",
        "zoning_policy": TEST_ZONING_POLICY,
        "auto_add_host_key": True,
        "virtual_fabric_id": TEST_VIRTUAL_FABRIC_ID,
        "port": TEST_PORT,
        "vsan": None,
    }

    fabric.get_endpoint_url_by_service_name = mock.Mock(
        return_value=TEST_ENDPOINT
    )

    fabric.fabric_ops = mock.Mock(
        side_effect=Exception("registration failed")
    )

    with pytest.raises(Exception, match="registration failed"):
        module.run()

    assert fabric.get_endpoint_url_by_service_name.called
    assert fabric.fabric_ops.called