import sys
import types
from contextlib import contextmanager
from unittest.mock import MagicMock, patch

from DashAI.back.credentials.github_credential import GithubCredential
from DashAI.back.credentials.huggingface_credential import HuggingFaceCredential
from DashAI.back.credentials.kaggle_credential import KaggleCredential


@contextmanager
def fake_kaggle(api_instance):
    """Install a stub ``kaggle`` package so the real one is never imported.

    The official ``kaggle`` package authenticates at import time and exits the
    process without credentials, so tests inject a fake module tree exposing a
    ``KaggleApi`` that returns ``api_instance``.
    """
    module_names = ("kaggle", "kaggle.api", "kaggle.api.kaggle_api_extended")
    saved = {name: sys.modules.get(name) for name in module_names}
    sys.modules["kaggle"] = types.ModuleType("kaggle")
    sys.modules["kaggle.api"] = types.ModuleType("kaggle.api")
    extended = types.ModuleType("kaggle.api.kaggle_api_extended")
    extended.KaggleApi = MagicMock(return_value=api_instance)
    sys.modules["kaggle.api.kaggle_api_extended"] = extended
    try:
        yield
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def test_huggingface_verify_success():
    cred = HuggingFaceCredential()
    with patch("huggingface_hub.HfApi") as hf_api:
        hf_api.return_value.whoami.return_value = {"name": "user"}
        assert cred.verify("hf_good") is True


def test_huggingface_verify_failure():
    cred = HuggingFaceCredential()
    with patch("huggingface_hub.HfApi") as hf_api:
        hf_api.return_value.whoami.side_effect = Exception("401")
        assert cred.verify("hf_bad") is False


def test_github_verify_success():
    cred = GithubCredential()
    with patch("requests.get") as get:
        get.return_value = MagicMock(status_code=200)
        assert cred.verify("ghp_good") is True


def test_github_verify_failure():
    cred = GithubCredential()
    with patch("requests.get") as get:
        get.return_value = MagicMock(status_code=401)
        assert cred.verify("ghp_bad") is False


def test_kaggle_verify_success():
    cred = KaggleCredential()
    api = MagicMock()
    api.authenticate.return_value = None
    api.competitions_list.return_value = []
    with fake_kaggle(api):
        assert cred.verify("user:key") is True


def test_kaggle_verify_failure():
    cred = KaggleCredential()
    api = MagicMock()
    api.competitions_list.side_effect = Exception("401")
    with fake_kaggle(api):
        assert cred.verify("user:badkey") is False


def test_kaggle_verify_malformed_key():
    cred = KaggleCredential()
    assert cred.verify("no-separator") is False
