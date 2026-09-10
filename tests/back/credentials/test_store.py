import pytest
from cryptography.fernet import Fernet
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.credentials.encryptor import CredentialEncryptor
from DashAI.back.credentials.store import CredentialStore
from DashAI.back.dependencies.database.models import Base


@pytest.fixture
def session_factory():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)


@pytest.fixture
def store(session_factory):
    encryptor = CredentialEncryptor(Fernet.generate_key())
    return CredentialStore(session_factory, encryptor)


def test_save_and_load_roundtrip(store):
    store.save("HuggingFaceCredential", "hf_token_123")
    assert store.load("HuggingFaceCredential") == "hf_token_123"


def test_save_marks_verified(store):
    store.save("HuggingFaceCredential", "hf_token_123")
    assert store.is_verified("HuggingFaceCredential") is True


def test_load_missing_returns_none(store):
    assert store.load("Missing") is None
    assert store.is_verified("Missing") is False


def test_save_is_upsert(store):
    store.save("HuggingFaceCredential", "old")
    store.save("HuggingFaceCredential", "new")
    assert store.load("HuggingFaceCredential") == "new"


def test_delete_removes_key(store):
    store.save("HuggingFaceCredential", "tok")
    store.delete("HuggingFaceCredential")
    assert store.load("HuggingFaceCredential") is None
    assert store.is_verified("HuggingFaceCredential") is False


def test_all_statuses(store):
    store.save("HuggingFaceCredential", "tok")
    store.save("GithubCredential", "ghp")
    assert store.all_statuses() == {
        "HuggingFaceCredential": True,
        "GithubCredential": True,
    }
