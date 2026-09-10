from pathlib import Path

import pytest
import torch

from DashAI.back.models.hugging_face.nllb_transformer import NllbTransformer


class DummyNllbTokenizer:
    def __init__(self):
        self.lang_code_to_id = {"spa_Latn": 100, "eng_Latn": 200}
        self.src_lang = "spa_Latn"
        self.unk_token_id = 0

    def __call__(self, text, truncation=True, padding="max_length", max_length=512):
        del truncation, padding
        n_tokens = min(max_length, max(1, len(str(text).split())))
        return {
            "input_ids": [1] * n_tokens + [0] * (max_length - n_tokens),
            "attention_mask": [1] * n_tokens + [0] * (max_length - n_tokens),
        }

    def decode(self, token_ids, skip_special_tokens=True):
        del token_ids, skip_special_tokens
        return "translated text"

    def convert_tokens_to_ids(self, token):
        return self.lang_code_to_id.get(token, 0)

    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "tokenizer.json").write_text("{}", encoding="utf-8")


class DummyNllbTokenizerNoLangMap:
    def __init__(self):
        self.src_lang = "spa_Latn"
        self.unk_token_id = 0
        self._token_to_id = {"spa_Latn": 100, "eng_Latn": 200}

    def __call__(self, text, truncation=True, padding="max_length", max_length=512):
        del truncation, padding
        n_tokens = min(max_length, max(1, len(str(text).split())))
        return {
            "input_ids": [1] * n_tokens + [0] * (max_length - n_tokens),
            "attention_mask": [1] * n_tokens + [0] * (max_length - n_tokens),
        }

    def decode(self, token_ids, skip_special_tokens=True):
        del token_ids, skip_special_tokens
        return "translated text"

    def convert_tokens_to_ids(self, token):
        return self._token_to_id.get(token, self.unk_token_id)


class DummyNllbModel:
    def __init__(self):
        self.device = torch.device("cpu")

    def generate(self, **kwargs):
        del kwargs
        return torch.tensor([[1, 2, 3]])

    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "weights.bin").write_bytes(b"weights")


class DummyConfig:
    def __init__(self):
        self.custom_params = {}

    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "config.json").write_text("{}", encoding="utf-8")


def _patch_transformers(monkeypatch, tokenizer_factory=DummyNllbTokenizer):
    from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer

    monkeypatch.setattr(
        AutoTokenizer,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: tokenizer_factory()),
    )
    monkeypatch.setattr(
        AutoModelForSeq2SeqLM,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyNllbModel()),
    )
    monkeypatch.setattr(
        AutoConfig,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyConfig()),
    )


def test_model_initialization(monkeypatch):
    _patch_transformers(monkeypatch)

    model = NllbTransformer(
        num_train_epochs=1,
        batch_size=2,
        learning_rate=2e-5,
        device="CPU",
        weight_decay=0.01,
        source_language="spa_Latn",
        target_language="eng_Latn",
        log_train_every_n_epochs=None,
        log_train_every_n_steps=None,
        log_validation_every_n_epochs=None,
        log_validation_every_n_steps=None,
    )

    assert model.model is not None
    assert model.tokenizer is not None
    assert model.model_name == "facebook/nllb-200-distilled-600M"
    assert model.source_language == "spa_Latn"
    assert model.target_language == "eng_Latn"
    assert model.fitted is False


def test_invalid_language_code_raises(monkeypatch):
    _patch_transformers(monkeypatch)

    with pytest.raises(ValueError, match="Unsupported source_language"):
        NllbTransformer(
            num_train_epochs=1,
            batch_size=2,
            learning_rate=2e-5,
            device="CPU",
            weight_decay=0.01,
            source_language="invalid_lang",
            target_language="eng_Latn",
            log_train_every_n_epochs=None,
            log_train_every_n_steps=None,
            log_validation_every_n_epochs=None,
            log_validation_every_n_steps=None,
        )


def test_model_initialization_without_lang_code_to_id(monkeypatch):
    _patch_transformers(monkeypatch, tokenizer_factory=DummyNllbTokenizerNoLangMap)

    model = NllbTransformer(
        num_train_epochs=1,
        batch_size=2,
        learning_rate=2e-5,
        device="CPU",
        weight_decay=0.01,
        source_language="spa_Latn",
        target_language="eng_Latn",
        log_train_every_n_epochs=None,
        log_train_every_n_steps=None,
        log_validation_every_n_epochs=None,
        log_validation_every_n_steps=None,
    )

    assert model.source_language_token_id == 100
    assert model.target_language_token_id == 200


def test_save_replaces_file_path_with_directory(monkeypatch, tmp_path):
    _patch_transformers(monkeypatch)

    model = NllbTransformer(
        num_train_epochs=1,
        batch_size=2,
        learning_rate=2e-5,
        device="CPU",
        weight_decay=0.01,
        source_language="spa_Latn",
        target_language="eng_Latn",
        log_train_every_n_epochs=None,
        log_train_every_n_steps=None,
        log_validation_every_n_epochs=None,
        log_validation_every_n_steps=None,
    )

    save_path = tmp_path / "run_path"
    save_path.write_bytes(b"\x80\x04stale")
    assert save_path.is_file()

    model.save(save_path)

    assert save_path.is_dir()
    assert (save_path / "weights.bin").exists()
