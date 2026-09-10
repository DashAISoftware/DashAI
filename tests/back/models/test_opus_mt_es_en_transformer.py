from pathlib import Path

import torch
from datasets import Dataset

from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
from DashAI.back.models.hugging_face.opus_mt_es_en_transformer import (
    OpusMtEsENTransformer,
)


class DummyTokenizer:
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

    def save_pretrained(self, save_directory):
        Path(save_directory).mkdir(parents=True, exist_ok=True)


class DummySeq2SeqModel:
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


def _patch_transformers(monkeypatch):
    from transformers import AutoConfig, AutoModelForSeq2SeqLM, AutoTokenizer

    monkeypatch.setattr(
        AutoTokenizer,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyTokenizer()),
    )
    monkeypatch.setattr(
        AutoModelForSeq2SeqLM,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummySeq2SeqModel()),
    )
    monkeypatch.setattr(
        AutoConfig,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyConfig()),
    )


def test_model_initialization(monkeypatch):
    _patch_transformers(monkeypatch)

    model = OpusMtEsENTransformer(
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

    assert model.model is not None
    assert model.tokenizer is not None
    assert model.model_name == "Helsinki-NLP/opus-mt-es-en"
    assert model.fitted is False


def test_tokenize_data(monkeypatch):
    _patch_transformers(monkeypatch)

    model = OpusMtEsENTransformer(
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

    x = to_dashai_dataset(Dataset.from_list([{"text": "hola mundo"}]))
    y = to_dashai_dataset(Dataset.from_list([{"class": "hello world"}]))
    tokenized_dataset = model.tokenize_data(x, y)

    assert "input_ids" in tokenized_dataset.features
    assert "attention_mask" in tokenized_dataset.features
    assert "labels" in tokenized_dataset.features
    assert len(tokenized_dataset) == len(x)


def test_save_replaces_file_path_with_directory(monkeypatch, tmp_path):
    _patch_transformers(monkeypatch)

    model = OpusMtEsENTransformer(
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

    save_path = tmp_path / "run_path"
    save_path.write_bytes(b"\x80\x04stale")
    assert save_path.is_file()

    model.save(save_path)

    assert save_path.is_dir()
    assert (save_path / "weights.bin").exists()
