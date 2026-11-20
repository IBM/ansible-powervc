import pytest
from unittest import mock

from ansible_collections.ibm.powervc.plugins.modules import storage
from ansible_collections.ibm.powervc.plugins.module_utils import crud_storage


TEST_STORAGE_ID = "id12ms_tier1_3"
TEST_HOST_IP = "192.168.68.86"
TEST_USER = "superuser"
TEST_PASSWORD = "secret_password"
TEST_AUTH_TOKEN = "test_auth_token"
TEST_TENANT_ID = "test_tenant_id"
TEST_ENDPOINT = "https://powervc.example.com:9000/v3/test_tenant_id"


def create_module():
    module = storage.StorageModule.__new__(storage.StorageModule)
    module.params = {}
    module.ansible = mock.Mock()
    module.ansible.check_mode = False
    module.no_log_values = set()

    module.conn = mock.Mock()
    module.conn.auth_token = TEST_AUTH_TOKEN
    module.conn.session = mock.Mock()
    module.conn.session.get_project_id.return_value = TEST_TENANT_ID
    module.conn.session.verify = True

    module.exit_json = mock.Mock()
    module.fail_json = mock.Mock()

    return module


# Test 1: Fetch all storage systems (standard summary)
def test_get_all_storage_summary(monkeypatch):
    module = create_module()
    module.params = {
        "state": "present",
        "id": None,
        "host": None,
        "detail": False,
        "extra_params": {},
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    mock_ops = mock.Mock(return_value={"changed": False, "result": {"hosts": []}})
    monkeypatch.setattr(storage, "storage_ops", mock_ops)

    module.run()

    mock_ops.assert_called_once_with(
        module=module,
        endpoint=TEST_ENDPOINT,
        authtoken=TEST_AUTH_TOKEN,
        tenant_id=TEST_TENANT_ID,
        verify=True,
        state="present",
        storage_id=None,
        body=None,
        detail=False,
    )
    module.exit_json.assert_called_once_with(changed=False, result={"hosts": []})


# Test 2: Fetch all storage providers with full details (storage-providers/detail)
def test_get_all_storage_detail(monkeypatch):
    module = create_module()
    module.params = {
        "state": "present",
        "id": None,
        "host": None,
        "detail": True,
        "extra_params": {},
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    mock_ops = mock.Mock(
        return_value={"changed": False, "result": {"storage_providers": [{"id": 1}]}}
    )
    monkeypatch.setattr(storage, "storage_ops", mock_ops)

    module.run()

    mock_ops.assert_called_once_with(
        module=module,
        endpoint=TEST_ENDPOINT,
        authtoken=TEST_AUTH_TOKEN,
        tenant_id=TEST_TENANT_ID,
        verify=True,
        state="present",
        storage_id=None,
        body=None,
        detail=True,
    )
    module.exit_json.assert_called_once()


# Test 3: Fetch specific storage with detail=True
def test_get_specific_storage_detail(monkeypatch):
    module = create_module()
    module.params = {
        "state": "present",
        "id": TEST_STORAGE_ID,
        "host": None,
        "detail": True,
        "extra_params": {},
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    mock_ops = mock.Mock(
        return_value={
            "changed": False,
            "result": {
                "storage_provider": {
                    "storage_hostname": TEST_STORAGE_ID,
                    "service": {"mirroring": "enabled", "mirror_ip": "192.168.100.23"},
                }
            },
        }
    )
    monkeypatch.setattr(storage, "storage_ops", mock_ops)

    module.run()

    mock_ops.assert_called_once_with(
        module=module,
        endpoint=TEST_ENDPOINT,
        authtoken=TEST_AUTH_TOKEN,
        tenant_id=TEST_TENANT_ID,
        verify=True,
        state="present",
        storage_id=TEST_STORAGE_ID,
        body=None,
        detail=True,
    )
    module.exit_json.assert_called_once()


# Test 4: Register SVC storage
def test_register_svc_storage(monkeypatch):
    module = create_module()
    module.params = {
        "state": "present",
        "id": None,
        "host": TEST_HOST_IP,
        "user": TEST_USER,
        "password": TEST_PASSWORD,
        "ssh_key": None,
        "type": "svc",
        "volume_pool": "Pool0",
        "name": "SVC-Storage",
        "auto_add_host_key": True,
        "extra_params": {},
        "restart": False,
        "detail": False,
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    mock_ops = mock.Mock(return_value={"changed": True, "msg": "Storage registered successfully"})
    monkeypatch.setattr(storage, "storage_ops", mock_ops)

    module.run()

    expected_body = {
        "host": {
            "registration": {
                "host_type": "svc",
                "access_ip": TEST_HOST_IP,
                "user_id": TEST_USER,
                "password": TEST_PASSWORD,
                "auto_add_host_key": True,
                "volume_pool_name": "Pool0",
                "host_display_name": "SVC-Storage",
            }
        }
    }
    mock_ops.assert_called_once_with(
        module=module,
        endpoint=TEST_ENDPOINT,
        authtoken=TEST_AUTH_TOKEN,
        tenant_id=TEST_TENANT_ID,
        verify=True,
        state="present",
        storage_id=None,
        body=expected_body,
        detail=False,
    )
    module.exit_json.assert_called_once()


# Test 5: Update SVC storage with secondary mirroring and GMCV in extra_params
def test_update_svc_storage_secondary_mirroring(monkeypatch):
    module = create_module()
    module.params = {
        "state": "present",
        "id": TEST_STORAGE_ID,
        "host": None,
        "user": None,
        "password": None,
        "ssh_key": None,
        "type": None,
        "volume_pool": None,
        "name": None,
        "auto_add_host_key": True,
        "restart": False,
        "detail": False,
        "extra_params": {
            "enable_mirror": True,
            "enable_gmcv": True,
            "mirror_access_ip": "192.168.100.23",
            "mirror_pool": "general-flash-1",
            "mirror_user_id": "superuser",
            "mirror_password": "secondary_secret",
            "mirror_private_key_data": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
        },
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    mock_ops = mock.Mock(return_value={"changed": True, "msg": "Updated"})
    monkeypatch.setattr(storage, "storage_ops", mock_ops)

    module.run()

    # Verify secret fields are masked into no_log_values
    assert "secondary_secret" in module.no_log_values
    assert "-----BEGIN RSA PRIVATE KEY-----\nMIIE..." in module.no_log_values

    expected_body = {
        "registration": {
            "enable_mirror": True,
            "enable_gmcv": True,
            "mirror_access_ip": "192.168.100.23",
            "mirror_pool": "general-flash-1",
            "mirror_user_id": "superuser",
            "mirror_password": "secondary_secret",
            "mirror_private_key_data": "-----BEGIN RSA PRIVATE KEY-----\nMIIE...",
        }
    }
    mock_ops.assert_called_once_with(
        module=module,
        endpoint=TEST_ENDPOINT,
        authtoken=TEST_AUTH_TOKEN,
        tenant_id=TEST_TENANT_ID,
        verify=True,
        state="present",
        storage_id=TEST_STORAGE_ID,
        body=expected_body,
        detail=False,
    )
    module.exit_json.assert_called_once()


# Test 6: Check Mode for storage operations
def test_storage_check_mode(monkeypatch):
    module = create_module()
    module.ansible.check_mode = True
    module.params = {
        "state": "absent",
        "id": TEST_STORAGE_ID,
        "detail": False,
        "extra_params": {},
    }

    monkeypatch.setattr(
        storage,
        "get_endpoint_url_by_service_name",
        mock.Mock(return_value=TEST_ENDPOINT),
    )

    module.run()

    module.exit_json.assert_called_once_with(
        changed=True,
        msg=f"[CHECK MODE] Would remove storage system {TEST_STORAGE_ID}",
    )


# Test 7: Error message extraction helper in crud_storage
def test_error_message_extraction():
    mock_resp = mock.Mock()
    mock_resp.json.return_value = {
        "badRequest": {"message": "Invalid secondary storage parameters"}
    }
    mock_resp.text = "Bad Request"

    err = crud_storage._extract_error_message(mock_resp)
    assert err == "Invalid secondary storage parameters"
