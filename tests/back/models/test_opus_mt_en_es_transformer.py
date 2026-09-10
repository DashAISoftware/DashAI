from pathlib import Path

import torch

from DashAI.back.models.hugging_face.opus_mt_en_es_transformer import (
    OpusMtEnESTransformer,
)


class DummyTokenizer:
    def __call__(self, text, truncation=True, padding="max_length", max_length=512):
        del text, truncation, padding, max_length
        return {"input_ids": [1, 2, 3], "attention_mask": [1, 1, 1]}

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

    model = OpusMtEnESTransformer(
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
    assert model.model_name == "Helsinki-NLP/opus-mt-en-es"
    assert model.fitted is False


def test_save_replaces_file_path_with_directory(monkeypatch, tmp_path):
    _patch_transformers(monkeypatch)

    model = OpusMtEnESTransformer(
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
