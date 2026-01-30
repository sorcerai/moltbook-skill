"""
Credential Manager Tests
TDD tests for isolated credential storage
"""
import os
import json
import tempfile
import shutil
from pathlib import Path

# Test configuration
TEST_CONFIG_DIR = tempfile.mkdtemp()
TEST_MEMORY_DIR = tempfile.mkdtemp()
CREDENTIALS_PATH = Path(TEST_CONFIG_DIR) / "credentials.json"

def setup():
    """Reset test environment"""
    if CREDENTIALS_PATH.exists():
        CREDENTIALS_PATH.unlink()

def teardown():
    """Cleanup test directories"""
    shutil.rmtree(TEST_CONFIG_DIR, ignore_errors=True)
    shutil.rmtree(TEST_MEMORY_DIR, ignore_errors=True)


# === TESTS ===

def test_store_api_key_in_config_only():
    """Given API key, should store in config file only"""
    setup()
    from credential_manager import CredentialManager
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    cm.store(api_key="test_api_key_12345", agent_id="agent_123")
    
    # Should exist in config
    assert CREDENTIALS_PATH.exists(), "Credentials file should exist"
    data = json.loads(CREDENTIALS_PATH.read_text())
    assert data.get("api_key") == "test_api_key_12345"
    assert data.get("agent_id") == "agent_123"


def test_load_from_config_file():
    """Given credential read, should load from isolated config file"""
    setup()
    from credential_manager import CredentialManager
    
    # Pre-populate credentials
    CREDENTIALS_PATH.parent.mkdir(parents=True, exist_ok=True)
    CREDENTIALS_PATH.write_text(json.dumps({
        "api_key": "loaded_key_xyz",
        "agent_id": "agent_456",
        "mode": "lurk"
    }))
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    creds = cm.load()
    
    assert creds["api_key"] == "loaded_key_xyz"
    assert creds["agent_id"] == "agent_456"
    assert creds["mode"] == "lurk"


def test_api_key_never_in_memory_files():
    """Given memory file write, should never include API key"""
    setup()
    from credential_manager import CredentialManager
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    cm.store(api_key="secret_key_do_not_leak", agent_id="agent_789")
    
    # Simulate memory file content
    memory_content = cm.get_safe_summary()
    
    assert "secret_key_do_not_leak" not in memory_content
    assert "agent_789" in memory_content  # ID is okay to log
    assert "[REDACTED]" in memory_content or "api_key" not in memory_content


def test_mode_persists_to_credentials():
    """Given mode update, should persist to credentials file"""
    setup()
    from credential_manager import CredentialManager
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    cm.store(api_key="key", agent_id="agent")
    
    cm.set_mode("engage")
    
    # Reload and verify
    data = json.loads(CREDENTIALS_PATH.read_text())
    assert data.get("mode") == "engage"
    
    cm.set_mode("active")
    data = json.loads(CREDENTIALS_PATH.read_text())
    assert data.get("mode") == "active"


def test_load_returns_none_when_no_credentials():
    """Given no credentials file, should return None"""
    setup()
    from credential_manager import CredentialManager
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    creds = cm.load()
    
    assert creds is None


def test_default_mode_is_lurk():
    """Given new credentials, default mode should be lurk"""
    setup()
    from credential_manager import CredentialManager
    
    cm = CredentialManager(config_dir=TEST_CONFIG_DIR)
    cm.store(api_key="key", agent_id="agent")
    
    creds = cm.load()
    assert creds.get("mode") == "lurk"


if __name__ == "__main__":
    tests = [
        test_store_api_key_in_config_only,
        test_load_from_config_file,
        test_api_key_never_in_memory_files,
        test_mode_persists_to_credentials,
        test_load_returns_none_when_no_credentials,
        test_default_mode_is_lurk,
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        finally:
            setup()  # Reset between tests
    
    teardown()
    print(f"\n{passed} passed, {failed} failed")
