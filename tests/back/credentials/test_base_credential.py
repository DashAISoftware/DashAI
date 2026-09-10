import pytest
from cryptography.fernet import Fernet
from kink import di
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from DashAI.back.credentials.base_credential import BaseCredential
from DashAI.back.credentials.encryptor import CredentialEncryptor
from DashAI.back.credentials.store import CredentialStore
from DashAI.back.dependencies.database.models import Base


class FakeCredential(BaseCredential):
    DISPLAY_NAME = "Fake"
    DESCRIPTION = "Fake credential for tests"
    last_seen_key = None

    def verify(self, key: str) -> bool:
        return key == "good"


@pytest.fixture(autouse=True)
def credential_store_in_di():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    session_factory = sessionmaker(bind=engine)
    encryptor = CredentialEncryptor(Fernet.generate_key())
    di["credential_store"] = CredentialStore(session_factory, encryptor)
    yield
    del di["credential_store"]


def test_auth_stores_valid_key():
    cred = FakeCredential()
    assert cred.auth("good") is True
    assert cred.get_key() == "good"
    assert cred.is_authenticated() is True


def test_auth_rejects_invalid_key():
    cred = FakeCredential()
    with pytest.raises(ValueError, match="Invalid credential"):
        cred.auth("bad")
    assert cred.get_key() is None
    assert cred.is_authenticated() is False


def test_apply_is_noop_without_key():
    cred = FakeCredential()
    # should not raise even though nothing is stored
    cred.apply()


def test_type_is_credential():
    assert FakeCredential.TYPE == "Credential"
