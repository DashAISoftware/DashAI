from pathlib import Path

from DashAI.back.credentials.encryptor import (
    CredentialEncryptor,
    load_or_create_key,
)


def test_encrypt_decrypt_roundtrip():
    key = load_or_create_key(Path("/nonexistent/path"), env_value=None, persist=False)
    enc = CredentialEncryptor(key)
    token = enc.encrypt("hf_secret_token")
    assert token != "hf_secret_token"
    assert enc.decrypt(token) == "hf_secret_token"


def test_load_or_create_key_uses_env_value(tmp_path):
    from cryptography.fernet import Fernet

    env_key = Fernet.generate_key().decode()
    key = load_or_create_key(tmp_path / "key", env_value=env_key)
    assert key == env_key.encode()


def test_load_or_create_key_persists_and_reuses(tmp_path):
    key_path = tmp_path / ".credentials_key"
    first = load_or_create_key(key_path, env_value=None)
    assert key_path.exists()
    second = load_or_create_key(key_path, env_value=None)
    assert first == second
