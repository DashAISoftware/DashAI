from pathlib import Path

from DashAI.back.models.hugging_face.distilbert_transformer import DistilBertTransformer


class DummyTokenizer:
    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "tokenizer.json").write_text("{}", encoding="utf-8")


class DummyConfig:
    def __init__(self):
        self.custom_params = {}

    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "config.json").write_text("{}", encoding="utf-8")


class DummySequenceClassificationModel:
    def save_pretrained(self, save_directory):
        save_path = Path(save_directory)
        save_path.mkdir(parents=True, exist_ok=True)
        (save_path / "weights.bin").write_bytes(b"weights")


def _patch_transformers(monkeypatch):
    from transformers import (
        AutoConfig,
        AutoModelForSequenceClassification,
        AutoTokenizer,
    )

    monkeypatch.setattr(
        AutoTokenizer,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyTokenizer()),
    )
    monkeypatch.setattr(
        AutoConfig,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummyConfig()),
    )
    monkeypatch.setattr(
        AutoModelForSequenceClassification,
        "from_pretrained",
        staticmethod(lambda *args, **kwargs: DummySequenceClassificationModel()),
    )


def test_save_replaces_file_path_with_directory(monkeypatch, tmp_path):
    _patch_transformers(monkeypatch)

    model = DistilBertTransformer(
        num_train_epochs=1,
        batch_size=2,
        learning_rate=5e-5,
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
    assert (save_path / "config.json").exists()
