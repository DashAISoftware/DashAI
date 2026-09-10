import numpy as np
import pytest
from PIL import Image

from DashAI.back.explainability.explainers.grad_cam import GradCam
from DashAI.back.explainability.explainers.occlusion_saliency import (
    OcclusionSaliency,
)
from DashAI.back.models.image_explainable_model import GradCamCompatibleModel

IMAGE_SIZE = 32


class _FakeImageValue:
    """Wraps a PIL image behind the DashAI image type interface."""

    def __init__(self, pil_image):
        self._pil_image = pil_image

    def to_pil(self):
        return self._pil_image


class _FakeImageDataset:
    """Minimal stand-in for a DashAIDataset holding one image column."""

    def __init__(self, images):
        self._rows = [{"image": _FakeImageValue(image)} for image in images]
        self.features = {"image": None}

    def __len__(self):
        return len(self._rows)

    def __getitem__(self, index):
        return self._rows[index]


class _ConvImageModel(GradCamCompatibleModel):
    """Tiny convolutional image classifier exposing the capability contract."""

    def __init__(self):
        import torch
        import torch.nn as nn

        torch.manual_seed(0)
        self.image_size = IMAGE_SIZE
        self.device = torch.device("cpu")
        self.idx_to_label = {0: "cat", 1: "dog"}
        self.model = nn.Sequential(
            nn.Conv2d(3, 4, 3, padding=1),
            nn.ReLU(),
            nn.AdaptiveAvgPool2d(4),
            nn.Flatten(),
            nn.Linear(4 * 4 * 4, 2),
        )

    def get_inference_transform(self):
        from torchvision import transforms

        return transforms.Compose(
            [
                transforms.Lambda(lambda img: img.convert("RGB")),
                transforms.Resize((self.image_size, self.image_size)),
                transforms.ToTensor(),
            ]
        )


class _MlpImageModel(_ConvImageModel):
    """Image model with no convolutional layers (like MLPImageClassifier)."""

    def __init__(self):
        import torch
        import torch.nn as nn

        super().__init__()
        torch.manual_seed(0)
        self.model = nn.Sequential(
            nn.Flatten(),
            nn.Linear(3 * IMAGE_SIZE * IMAGE_SIZE, 2),
        )


@pytest.fixture(name="images")
def images_fixture():
    rng = np.random.RandomState(0)
    return [
        Image.fromarray(
            rng.randint(0, 255, size=(IMAGE_SIZE, IMAGE_SIZE, 3), dtype=np.uint8)
        )
        for _ in range(2)
    ]


def _assert_image_explanation(explanation, n_instances):
    assert explanation["metadata"]["target_names"] == ["cat", "dog"]
    instance_keys = [key for key in explanation if key != "metadata"]
    assert len(instance_keys) == n_instances

    for key in instance_keys:
        instance = explanation[key]
        heatmap = np.asarray(instance["heatmap"])
        assert heatmap.shape == (IMAGE_SIZE, IMAGE_SIZE)
        assert heatmap.min() >= 0.0
        assert heatmap.max() <= 1.0
        assert np.asarray(instance["image"]).shape == (IMAGE_SIZE, IMAGE_SIZE, 3)
        assert instance["predicted_class"] in (0, 1)
        assert len(instance["model_prediction"]) == 2


@pytest.mark.parametrize("method", ["gradcam", "gradcam++"])
def test_grad_cam(images, method):
    model = _ConvImageModel()
    explainer = GradCam(model, method=method)
    explainer.fit((None, None))

    explanation = explainer.explain_instance(_FakeImageDataset(images))
    _assert_image_explanation(explanation, len(images))

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(images)
    for group in groups:
        assert [a.type for a in group.artifacts] == ["plotly"]


def test_grad_cam_rejects_non_convolutional_models(images):
    explainer = GradCam(_MlpImageModel())
    explainer.fit((None, None))

    with pytest.raises(ValueError, match="convolutional"):
        explainer.explain_instance(_FakeImageDataset(images))


def test_occlusion_saliency(images):
    model = _ConvImageModel()
    explainer = OcclusionSaliency(model, patch_size=8, stride=8)
    explainer.fit((None, None))

    explanation = explainer.explain_instance(_FakeImageDataset(images))
    _assert_image_explanation(explanation, len(images))

    plot = explainer.plot(explanation)
    assert len(plot) == 1
    groups = plot[0].groups
    assert len(groups) == len(images)
    for group in groups:
        assert [a.type for a in group.artifacts] == ["plotly"]


def test_occlusion_saliency_works_without_conv_layers(images):
    # Unlike Grad-CAM, occlusion only needs forward passes.
    explainer = OcclusionSaliency(_MlpImageModel(), patch_size=8, stride=8)
    explainer.fit((None, None))

    explanation = explainer.explain_instance(_FakeImageDataset(images))
    _assert_image_explanation(explanation, len(images))
