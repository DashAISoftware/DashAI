"""Tests that OpusMtTransformerMixin subclasses expose download metadata."""

from unittest.mock import MagicMock, patch

import pytest
from kink import di

from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)


@pytest.fixture
def component_root(tmp_path):
    """Inject a temporary COMPONENT_PATH into the kink DI container."""
    sentinel = object()
    old = di["config"] if "config" in di else sentinel  # noqa: SIM401
    di["config"] = {"COMPONENT_PATH": str(tmp_path)}
    yield tmp_path
    if old is sentinel:
        del di["config"]
    else:
        di["config"] = old


def test_opus_mt_is_downloadable():
    assert issubclass(OpusMtEnESTransformer, HFDownloadableMixin)
    assert OpusMtEnESTransformer.REQUIRES_DOWNLOAD is True
    assert OpusMtEnESTransformer.DOWNLOAD_SIZE_BYTES is not None


def test_opus_mt_hf_repos_derived_from_model_name():
    assert OpusMtEnESTransformer.hf_repos() == [("Helsinki-NLP/opus-mt-en-es", "model")]


def test_opus_mt_metadata_flags_download():
    meta = OpusMtEnESTransformer.get_metadata()
    assert meta["requires_download"] is True
    assert meta["download_size_bytes"] == OpusMtEnESTransformer.DOWNLOAD_SIZE_BYTES


def test_opus_mt_is_downloaded_uses_component_dir(component_root):
    assert OpusMtEnESTransformer.is_downloaded() is False

    repo_dir = component_root / "OpusMtEnESTransformer" / "opus-mt-en-es"
    repo_dir.mkdir(parents=True)
    (repo_dir / "config.json").write_text("{}")
    assert OpusMtEnESTransformer.is_downloaded() is True


# ---------------------------------------------------------------------------
# Self-contained run tests (no real weights required)
# ---------------------------------------------------------------------------


@pytest.fixture
def component_root_for_save_load(tmp_path):
    """Inject a temporary COMPONENT_PATH so _repo_dir resolves without touching
    the real filesystem or requiring a real download.
    """
    sentinel = object()
    old = di["config"] if "config" in di else sentinel  # noqa: SIM401
    di["config"] = {"COMPONENT_PATH": str(tmp_path)}
    yield tmp_path
    if old is sentinel:
        del di["config"]
    else:
        di["config"] = old


def test_save_persists_tokenizer(tmp_path, component_root_for_save_load):
    """save() must call both model.save_pretrained and tokenizer.save_pretrained."""
    mock_tokenizer = MagicMock()
    mock_model = MagicMock()

    with (
        patch("transformers.AutoTokenizer") as tok_cls,
        patch("transformers.AutoModelForSeq2SeqLM"),
        patch("transformers.AutoConfig") as cfg_cls,
    ):
        tok_cls.from_pretrained.return_value = mock_tokenizer

        instance = OpusMtEnESTransformer(
            model=mock_model,
            pretrained_dir=str(tmp_path),
            num_train_epochs=1,
            batch_size=2,
            learning_rate=2e-5,
            device="CPU",
            weight_decay=0.01,
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )
        instance.fitted = True

        save_dir = tmp_path / "run"
        cfg_cls.from_pretrained.return_value = MagicMock()

        instance.save(save_dir)

    mock_model.save_pretrained.assert_called_once_with(save_dir)
    mock_tokenizer.save_pretrained.assert_called_once_with(save_dir)


def test_load_tokenizer_from_run_dir_not_download_folder(
    tmp_path, component_root_for_save_load
):
    """load() must load the tokenizer from the run dir, not the component download
    folder. This verifies that trained runs are self-contained.
    """
    run_dir = tmp_path / "my_run"
    run_dir.mkdir()

    mock_model = MagicMock()
    mock_tokenizer = MagicMock()
    mock_config = MagicMock()
    mock_config.custom_params = {
        "num_train_epochs": 1,
        "batch_size": 2,
        "learning_rate": 2e-5,
        "device": "CPU",
        "weight_decay": 0.01,
        "fitted": True,
    }

    with (
        patch("transformers.AutoTokenizer") as tok_cls,
        patch("transformers.AutoModelForSeq2SeqLM") as model_cls,
        patch("transformers.AutoConfig") as cfg_cls,
    ):
        tok_cls.from_pretrained.return_value = mock_tokenizer
        model_cls.from_pretrained.return_value = mock_model
        cfg_cls.from_pretrained.return_value = mock_config

        loaded = OpusMtEnESTransformer.load(run_dir)

    # The tokenizer must be loaded from the run dir.
    tok_cls.from_pretrained.assert_called_once_with(str(run_dir))

    # The component download folder (under COMPONENT_PATH) must NOT be used.
    component_download_dir = str(
        component_root_for_save_load / "OpusMtEnESTransformer" / "opus-mt-en-es"
    )
    for call in tok_cls.from_pretrained.call_args_list:
        assert call.args[0] != component_download_dir, (
            "tokenizer was loaded from the component download folder, not the run dir"
        )

    assert loaded.fitted is True
