"""Shared helpers for image-classification explainers.

These helpers define the (minimal) white box capability contract image
explainers rely on:

- ``model.model`` is the underlying ``torch.nn.Module``.
- ``model.get_inference_transform()`` returns the exact transform the
  model applies to input images (enforced by the image explainable model
  mixins in ``DashAI.back.models.image_explainable_model``).
- ``model.idx_to_label`` maps class indices to label names.
"""

from typing import Any, List

from DashAI.back.core.artifacts import PlotlyArtifact


def get_torch_module(model: Any):
    """Return the underlying ``torch.nn.Module`` of a DashAI image model.

    Parameters
    ----------
    model : Any
        The DashAI model wrapper.

    Returns
    -------
    torch.nn.Module
        The trained torch module.

    Raises
    ------
    ValueError
        If the model does not expose a torch module.
    """
    import torch

    module = getattr(model, "model", None)
    if module is None or not isinstance(module, torch.nn.Module):
        raise ValueError(
            "This explainer requires a model exposing its torch module via "
            f"the 'model' attribute; got {type(model).__name__}."
        )
    return module


def get_transform(model: Any):
    """Return the model's inference transform.

    Models compatible with image explainers implement
    ``get_inference_transform`` (enforced by the
    ``OcclusionSaliencyCompatibleModel`` / ``GradCamCompatibleModel``
    mixins), exposing the exact preprocessing they apply to input images.

    Parameters
    ----------
    model : Any
        The DashAI model wrapper.

    Returns
    -------
    Callable
        A transform mapping a PIL image to a normalized tensor.

    Raises
    ------
    ValueError
        If the model does not implement ``get_inference_transform``.
    """
    transform_factory = getattr(model, "get_inference_transform", None)
    if transform_factory is None:
        raise ValueError(
            "This explainer requires a model implementing "
            "'get_inference_transform' (see the image explainable model "
            f"mixins); got {type(model).__name__}."
        )
    return transform_factory()


def get_target_names(model: Any, y_dataset) -> List[str]:
    """Resolve class names in the model's class-index order.

    Prefers the model's ``idx_to_label`` mapping (which reflects the label
    order used at training time) and falls back to the sorted categories of
    the target column.

    Parameters
    ----------
    model : Any
        The DashAI model wrapper.
    y_dataset : Any
        Target splits; ``y_dataset["train"]`` must expose ``column_names``
        and ``types``.

    Returns
    -------
    List[str]
        Class names indexed by model output position.
    """
    idx_to_label = getattr(model, "idx_to_label", None)
    if idx_to_label:
        return [str(idx_to_label[key]) for key in sorted(idx_to_label)]

    y_train = y_dataset["train"]
    output_column = y_train.column_names[0]
    return sorted(str(c) for c in y_train.types[output_column].categories)


def iter_pil_images(instances):
    """Yield the PIL image of each row in an image dataset.

    Parameters
    ----------
    instances : Any
        A DashAIDataset (or compatible) whose first column holds images
        exposing ``to_pil()``.

    Yields
    ------
    PIL.Image.Image
        Each image converted to RGB.
    """
    image_column = list(instances.features.keys())[0]
    for index in range(len(instances)):
        yield instances[index][image_column].to_pil().convert("RGB")


def heatmap_overlay_artifact(
    image_uint8,
    heatmap,
    title: str,
    subtitle: str,
) -> PlotlyArtifact:
    """Build a plotly artifact with a jet heatmap blended over an image.

    Parameters
    ----------
    image_uint8 : array like
        RGB image of shape (H, W, 3), uint8 values.
    heatmap : array like
        Saliency map of shape (H, W) with values in [0, 1].
    title : str
        Artifact title (shown in the instance selector).
    subtitle : str
        Figure title (e.g. predicted class and probability).

    Returns
    -------
    PlotlyArtifact
        The plotly artifact with the blended overlay figure.
    """
    import numpy as np
    import plotly.graph_objs as go

    image = np.asarray(image_uint8, dtype=np.float32) / 255.0
    cam = np.clip(np.asarray(heatmap, dtype=np.float32), 0.0, 1.0)

    # Jet like colormap, avoids a matplotlib/cv2 dependency at plot time.
    red = np.clip(1.5 - np.abs(4 * cam - 3), 0, 1)
    green = np.clip(1.5 - np.abs(4 * cam - 2), 0, 1)
    blue = np.clip(1.5 - np.abs(4 * cam - 1), 0, 1)
    colored = np.stack([red, green, blue], axis=-1)

    blended = (0.5 * image + 0.5 * colored) * 255.0
    blended = blended.astype(np.uint8)

    fig = go.Figure(go.Image(z=blended))
    fig.update_layout(
        title={"text": subtitle, "font": {"size": 14}},
        margin={"l": 10, "r": 10, "t": 50, "b": 10},
        xaxis={"visible": False},
        yaxis={"visible": False},
    )

    return PlotlyArtifact(payload=fig, title=title)
