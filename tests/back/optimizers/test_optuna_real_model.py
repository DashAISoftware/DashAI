"""The same wiring, but against a model that ships with DashAI.

`test_optuna_pruning_integration.py` proves the outcome — Optuna records
trials as PRUNED — using a stand-in model whose training loop is three lines.
That is the right shape for asserting a pruning verdict deterministically, but
it cannot answer the question that matters for this feature: does the number a
pruner needs actually appear when a *real* model trains?

It did not. The epoch loops guard their validation metrics behind
`if x_validation is not None`, and `optimize` never passed validation data, so
`calculate_metrics(split=VALIDATION, level=EPOCH)` was skipped for every epoch
of every trial. Nothing was reported, so nothing could ever be pruned — no
matter what the pruner was.

This file uses `MLPImageClassifier` unmodified: its real `train`, its real
epoch loop, its real `calculate_metrics`, and the real `Accuracy` metric, on a
small synthetic image dataset. The only stub is `_save_metrics`, which needs a
database and is not what this proves.

The dataset is tiny (24 images of 16x16) and the models are three epochs wide
on purpose: this is a wiring test, and it should not cost a minute of CI.
"""

import os
import tempfile
import zipfile

import numpy as np
import pytest
from PIL import Image

from DashAI.back.core.enums.metrics import LevelEnum, SplitEnum
from DashAI.back.dataloaders.classes.dashai_dataset import (
    select_columns,
    split_dataset,
    split_indexes,
)
from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader
from DashAI.back.evaluation.holdout import HoldoutEvaluationStrategy
from DashAI.back.metrics.classification.accuracy import Accuracy
from DashAI.back.models.mlp_image_classifier import MLPImageClassifier
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer


def _holdout_evaluate(model, input_dataset, output_dataset, metric):
    """The real holdout evaluation path, on a strategy with no factory.

    `evaluate` reads which partitions its strategy scores, so it needs a real
    instance rather than None for self. Building one through __init__ would
    need a `ModelFactory` this test does not have, and does not need: the only
    thing read off the instance is a class attribute.
    """
    strategy = HoldoutEvaluationStrategy.__new__(HoldoutEvaluationStrategy)
    return strategy.evaluate(model, input_dataset, output_dataset, metric)


EPOCHS = 3
N_TRIALS = 3


@pytest.fixture(scope="module")
def image_splits(tmp_path_factory):
    """24 synthetic images in three classes, split train/test/validation.

    Each class is a different dominant colour channel over noise, so the
    problem is learnable. It does not need to be learned well — this asserts
    that per-epoch scores reach Optuna, not that they are good.
    """
    rng = np.random.default_rng(0)
    tmp = tmp_path_factory.mktemp("images")
    img_dir = tmp / "imgs"
    for cls in range(3):
        cls_dir = img_dir / f"class_{cls}"
        cls_dir.mkdir(parents=True)
        for i in range(8):
            arr = rng.integers(0, 120, (16, 16, 3), dtype=np.int16)
            arr[:, :, cls] += 120
            Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8)).save(
                cls_dir / f"img_{i}.png"
            )

    zip_path = tmp / "imgs.zip"
    with zipfile.ZipFile(zip_path, "w") as zf:
        for root, _, files in os.walk(img_dir):
            for f in files:
                full = os.path.join(root, f)
                zf.write(full, os.path.relpath(full, img_dir))

    dataset = ImageDataLoader().load_data(
        filepath_or_buffer=str(zip_path),
        temp_path=tempfile.mkdtemp(),
        params={},
    )
    train_idx, test_idx, val_idx = split_indexes(
        total_rows=dataset.num_rows, train_size=0.5, test_size=0.25, val_size=0.25
    )
    split = split_dataset(
        dataset,
        train_indexes=train_idx,
        test_indexes=test_idx,
        val_indexes=val_idx,
    )
    x, y = select_columns(split, ["image"], ["label"])
    return split_dataset(x), split_dataset(y)


def _model():
    model = MLPImageClassifier(
        epochs=EPOCHS, learning_rate=0.01, hidden_dims=[8], image_size=16
    )
    model.run_id = 1
    model.x_data = None
    model.y_data = None
    model.train_metrics = None
    model.validation_metrics = [Accuracy]
    model.test_metrics = None
    # Persistence needs a database and is not what this proves.
    model._save_metrics = lambda **kwargs: None
    return model


def test_a_real_model_reports_every_epoch_to_the_trial(image_splits):
    """Each trial must carry one intermediate value per epoch.

    This is the assertion that fails without the fix: with no validation data
    reaching `train`, `intermediate_values` is empty for every trial, and an
    empty history is a pruner that can never fire.

    Pruning is disabled here on purpose. Whether a given trial deserves to be
    cut is the pruner's policy and is asserted next door with a deterministic
    stand-in; what is under test here is that a real model produces the
    evidence that policy runs on.
    """
    model = _model()
    x, y = image_splits

    optimizer = OptunaOptimizer(
        n_trials=N_TRIALS, sampler="RandomSampler", pruner="None"
    )
    optimizer.optimize(
        model,
        x,
        y,
        [(model, "learning_rate", (1e-3, 5e-2), "number")],
        {"class": Accuracy, "metadata": {"maximize": True}},
        _holdout_evaluate,
    )

    reported = [len(t.intermediate_values) for t in optimizer.study.trials]
    assert reported == [EPOCHS] * N_TRIALS, (
        f"trials reported {reported} epoch scores, expected {EPOCHS} each. "
        "An empty history means the epoch loop skipped its validation metrics, "
        "which is what left the pruner with nothing to decide on."
    )


def test_without_validation_data_nothing_is_reported(image_splits):
    """The negative control, and the bug this feature had, in one call.

    Training a real model without validation data must leave the reporter
    untouched: the epoch loop skips `calculate_metrics(VALIDATION, EPOCH)`
    entirely. This is exactly what `optimize` used to do on every trial, so if
    this test ever starts reporting, the assertion above stops proving that
    `optimize` passes the data.
    """
    model = _model()
    x, y = image_splits
    calls = []
    model._epoch_reporter = lambda results, step: calls.append((results, step))

    model.train(x["train"], y["train"])

    assert calls == [], (
        "the reporter fired without validation data, so the assertion that "
        "`optimize` must pass it no longer distinguishes anything"
    )


def test_the_hook_only_fires_for_validation_epochs(image_splits):
    """Train-split and step-level metrics must not reach the pruner.

    A pruner fed the training score prunes on how well the model memorises,
    and one fed per-step noise prunes on a number that has not settled.
    """
    model = _model()
    x, y = image_splits
    seen = []
    model._epoch_reporter = lambda results, step: seen.append(step)

    model.train(x["train"], y["train"], x["validation"], y["validation"])

    assert seen == list(range(1, EPOCHS + 1)), (
        f"reported steps were {seen}; expected one per epoch, validation only"
    )


def test_calculate_metrics_reaches_the_hook_at_epoch_level(image_splits):
    """Guards the hook against the levels it must ignore, on the real model."""
    model = _model()
    x, y = image_splits
    model.train(x["train"], y["train"])

    seen = []
    model._epoch_reporter = lambda results, step: seen.append((results, step))

    for split, level in (
        (SplitEnum.TRAIN, LevelEnum.EPOCH),
        (SplitEnum.VALIDATION, LevelEnum.STEP),
        (SplitEnum.VALIDATION, LevelEnum.TRIAL),
    ):
        model.calculate_metrics(
            split=split,
            level=level,
            x_data=x["validation"],
            y_data=y["validation"],
            log_index=1,
        )
    assert seen == [], f"the hook fired for {seen}, which the pruner must not see"

    model.calculate_metrics(
        split=SplitEnum.VALIDATION,
        level=LevelEnum.EPOCH,
        x_data=x["validation"],
        y_data=y["validation"],
        log_index=1,
    )
    assert len(seen) == 1
    results, step = seen[0]
    assert step == 1
    assert Accuracy.__name__ in results
