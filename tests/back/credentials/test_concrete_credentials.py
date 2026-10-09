import os
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
    ``KaggleApi`` that returns ``api_instance``.  The module-level ``kaggle.api``
    singleton is set to ``api_instance`` so ``apply()`` can re-authenticate it.
    """
    module_names = ("kaggle", "kaggle.api", "kaggle.api.kaggle_api_extended")
    saved = {name: sys.modules.get(name) for name in module_names}
    kaggle_mod = types.ModuleType("kaggle")
    kaggle_mod.api = api_instance
    sys.modules["kaggle"] = kaggle_mod
    api_mod = types.ModuleType("kaggle.api")
    sys.modules["kaggle.api"] = api_mod
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
        for env_var in ("KAGGLE_API_TOKEN", "KAGGLE_USERNAME", "KAGGLE_KEY"):
            os.environ.pop(env_var, None)


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
    api.config_values = {"auth_method": "ACCESS_TOKEN"}
    api.authenticate.return_value = None
    with fake_kaggle(api):
        assert cred.verify("KGAT_good_token") is True
        assert os.environ.get("KAGGLE_API_TOKEN") == "KGAT_good_token"


def test_kaggle_verify_failure():
    cred = KaggleCredential()
    api = MagicMock()
    api.config_values = {"auth_method": "LEGACY_API_KEY"}
    api.authenticate.return_value = None
    with fake_kaggle(api):
        assert cred.verify("KGAT_bad_token") is False


def test_kaggle_verify_invalid_token_exits():
    cred = KaggleCredential()
    api = MagicMock()
    api.authenticate.side_effect = SystemExit(1)
    with fake_kaggle(api):
        assert cred.verify("KGAT_expired_token") is False


def test_kaggle_verify_empty_token():
    cred = KaggleCredential()
    assert cred.verify("") is False


def test_kaggle_apply_sets_token_and_reauths():
    cred = KaggleCredential()
    api = MagicMock()
    api.config_values = {"auth_method": "ACCESS_TOKEN"}
    with fake_kaggle(api), patch.object(cred, "get_key", return_value="KGAT_stored"):
        cred.apply()
        assert os.environ.get("KAGGLE_API_TOKEN") == "KGAT_stored"
    api.authenticate.assert_called()
