import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.explainers.image_explainer_utils import (
    get_target_names,
    get_torch_module,
    get_transform,
    heatmap_overlay_artifact,
    iter_pil_images,
)
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel


class OcclusionSaliencySchema(BaseSchema):
    """Schema for the Occlusion Saliency explainer hyperparameters.

    Configures the size and stride of the occlusion patch, in pixels of the
    model's input resolution.
    """

    patch_size: schema_field(
        int_field(ge=4, le=128),
        placeholder=16,
        description=MultilingualString(
            en=(
                "Side (in pixels) of the square patch that is occluded at "
                "each position. Smaller patches give finer maps but require "
                "more model evaluations."
            ),
            es=(
                "Lado (en píxeles) del parche cuadrado que se ocluye en cada "
                "posición. Parches más pequeños dan mapas más finos pero "
                "requieren más evaluaciones del modelo."
            ),
            pt=(
                "Lado (em pixels) do patch quadrado ocluído em cada posição. "
                "Patches menores dão mapas mais finos, mas requerem mais "
                "avaliações do modelo."
            ),
            zh="每个位置遮挡的正方形补丁的边长（像素）。较小的补丁产生更精细的图，但需要更多模型评估。",
            de=(
                "Seitenlänge (in Pixeln) des quadratischen Patches, der an "
                "jeder Position verdeckt wird. Kleinere Patches ergeben "
                "feinere Karten, erfordern aber mehr Modellauswertungen."
            ),
        ),
        alias=MultilingualString(
            en="Patch size",
            es="Tamaño del parche",
            pt="Tamanho do patch",
            zh="补丁大小",
            de="Patchgröße",
        ),
    )  # type: ignore

    stride: schema_field(
        int_field(ge=2, le=64),
        placeholder=8,
        description=MultilingualString(
            en=(
                "Step (in pixels) between consecutive patch positions. "
                "Smaller strides give smoother maps but require more model "
                "evaluations."
            ),
            es=(
                "Paso (en píxeles) entre posiciones consecutivas del parche. "
                "Pasos más pequeños dan mapas más suaves pero requieren más "
                "evaluaciones del modelo."
            ),
            pt=(
                "Passo (em pixels) entre posições consecutivas do patch. "
                "Passos menores dão mapas mais suaves, mas requerem mais "
                "avaliações do modelo."
            ),
            zh="连续补丁位置之间的步长（像素）。较小的步长产生更平滑的图，但需要更多模型评估。",
            de=(
                "Schrittweite (in Pixeln) zwischen aufeinanderfolgenden "
                "Patchpositionen. Kleinere Schritte ergeben glattere Karten, "
                "erfordern aber mehr Modellauswertungen."
            ),
        ),
        alias=MultilingualString(
            en="Stride",
            es="Paso",
            pt="Passo",
            zh="步长",
            de="Schrittweite",
        ),
    )  # type: ignore


class OcclusionSaliency(BaseLocalExplainer):
    """Perturbation-based saliency maps for image classifiers.

    Slides a gray patch over the image and records how much the predicted
    class probability drops at each position. Regions whose occlusion causes
    a large drop are the ones the model relied on. Unlike Grad-CAM, this
    method needs no gradients or convolutional layers, so it works with every
    DashAI image classifier including the MLP; the trade-off is one model
    evaluation per patch position.

    References
    ----------
    - [1] Zeiler, M.D. & Fergus, R. (2014). "Visualizing and Understanding
           Convolutional Networks." ECCV 2014. https://arxiv.org/abs/1311.2901
    """

    DISPLAY_NAME = MultilingualString(
        en="Occlusion Saliency",
        es="Saliencia por oclusión",
        pt="Saliência por oclusão",
        zh="遮挡显著性",
        de="Okklusions-Salienz",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Slides a gray patch over the image and maps how much each "
            "region's occlusion lowers the predicted class probability."
        ),
        es=(
            "Desliza un parche gris sobre la imagen y mapea cuánto baja la "
            "probabilidad de la clase predicha al ocluir cada región."
        ),
        pt=(
            "Desliza um patch cinza sobre a imagem e mapeia o quanto a "
            "oclusão de cada região reduz a probabilidade da classe prevista."
        ),
        zh="在图像上滑动灰色补丁，映射遮挡每个区域对预测类别概率的降低程度。",
        de=(
            "Schiebt einen grauen Patch über das Bild und kartiert, wie stark "
            "die Verdeckung jeder Region die vorhergesagte "
            "Klassenwahrscheinlichkeit senkt."
        ),
    )
    COLOR = "#AD1457"
    SCHEMA = OcclusionSaliencySchema

    def __init__(
        self,
        model: BaseModel,
        patch_size: int = 16,
        stride: int = 8,
    ) -> None:
        """Initialize a new instance of an OcclusionSaliency explainer.

        Parameters
        ----------
        model : BaseModel
            Image classification model to be explained.
        patch_size : int
            Side of the occluded square patch, in pixels.
        stride : int
            Step between consecutive patch positions, in pixels.
        """
        super().__init__(model)
        self.patch_size = patch_size
        self.stride = stride

    def fit(self, background_dataset, **kwargs):
        """Store class names in the model's class-index order.

        Parameters
        ----------
        background_dataset : Tuple[DatasetDict, DatasetDict]
            Tuple ``(x, y)`` with the dataset splits.
        **kwargs : Any
            Ignored; present for interface compatibility.

        Returns
        -------
        OcclusionSaliency
            The fitted explainer instance (``self``).
        """
        _, y = background_dataset
        self.metadata = {"target_names": get_target_names(self.model, y)}
        return self

    def _occlusion_map(self, module, tensor, predicted_class, device):
        """Compute the probability-drop map for one image tensor.

        Parameters
        ----------
        module : torch.nn.Module
            The model's torch module in eval mode.
        tensor : torch.Tensor
            Input tensor of shape (1, C, H, W).
        predicted_class : int
            Class whose probability drop is measured.
        device : torch.device
            Device to run the evaluations on.

        Returns
        -------
        np.ndarray
            Saliency map of shape (H, W), normalized to [0, 1].
        """
        import numpy as np
        import torch

        _, _, height, width = tensor.shape
        baseline = tensor.mean(dim=(2, 3), keepdim=True)

        with torch.no_grad():
            base_prob = torch.softmax(module(tensor), dim=1)[0, predicted_class]
        base_prob = float(base_prob)

        positions = [
            (top, left)
            for top in range(0, max(height - self.patch_size, 0) + 1, self.stride)
            for left in range(0, max(width - self.patch_size, 0) + 1, self.stride)
        ]

        drops = np.zeros((height, width), dtype=np.float32)
        counts = np.zeros((height, width), dtype=np.float32)

        batch_size = 32
        with torch.no_grad():
            for start in range(0, len(positions), batch_size):
                batch_positions = positions[start : start + batch_size]
                occluded = tensor.repeat(len(batch_positions), 1, 1, 1)
                for j, (top, left) in enumerate(batch_positions):
                    occluded[
                        j,
                        :,
                        top : top + self.patch_size,
                        left : left + self.patch_size,
                    ] = baseline[0]
                probs = torch.softmax(module(occluded.to(device)), dim=1)[
                    :, predicted_class
                ]
                for j, (top, left) in enumerate(batch_positions):
                    drop = base_prob - float(probs[j])
                    drops[
                        top : top + self.patch_size,
                        left : left + self.patch_size,
                    ] += drop
                    counts[
                        top : top + self.patch_size,
                        left : left + self.patch_size,
                    ] += 1.0

        saliency = drops / np.maximum(counts, 1.0)
        saliency = np.clip(saliency, 0.0, None)
        max_value = saliency.max()
        if max_value > 0:
            saliency = saliency / max_value
        return saliency

    def explain_instance(self, instances):
        """Compute an occlusion saliency map for each image.

        Parameters
        ----------
        instances : DashAIDataset
            Images to be explained; the first column must contain images.

        Returns
        -------
        dict
            Dictionary with, for each image, the resized image, the saliency
            map and the model prediction.
        """
        import numpy as np
        import torch

        module = get_torch_module(self.model)
        transform = get_transform(self.model)
        image_size = int(getattr(self.model, "image_size", 224))
        device = getattr(self.model, "device", torch.device("cpu"))

        module = module.to(device).eval()

        explanation = {"metadata": self.metadata}
        for i, pil_image in enumerate(iter_pil_images(instances)):
            tensor = transform(pil_image).unsqueeze(0).to(device)

            with torch.no_grad():
                probs = torch.softmax(module(tensor), dim=1)[0]
            predicted_class = int(torch.argmax(probs))

            saliency = self._occlusion_map(module, tensor, predicted_class, device)

            resized = pil_image.resize((image_size, image_size))
            explanation[i] = {
                "image": np.asarray(resized, dtype=np.uint8).tolist(),
                "heatmap": np.round(saliency, 4).tolist(),
                "model_prediction": np.round(probs.detach().cpu().numpy(), 4).tolist(),
                "predicted_class": predicted_class,
            }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each image as a saliency overlay.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained image,
            each holding that image's saliency overlay.
        """
        import numpy as np

        exp = explanation.copy()
        metadata = exp.pop("metadata")
        target_names = metadata["target_names"]

        groups = []
        for i in exp:
            instance = exp[i]
            predicted_class = instance["predicted_class"]
            predicted_name = target_names[predicted_class]
            predicted_prob = float(
                np.round(instance["model_prediction"][predicted_class], 3)
            )

            title = f"Image {int(i) + 1}"
            subtitle = f"Occlusion saliency for {predicted_name} (p={predicted_prob})"
            overlay = heatmap_overlay_artifact(
                instance["image"], instance["heatmap"], title, subtitle
            )
            groups.append(ArtifactGroup(title=title, artifacts=[overlay]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction the saliency overlay explains.

        Names the predicted class and its probability (the same values used
        to build the overlay's subtitle in :meth:`plot`).

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain_instance`.
        explainer_output : ArtifactGroup
            The group previously returned by :meth:`plot`, titled
            ``"Image {n}"``.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised "Image N" group.
        """
        match = re.match(r"Image (\d+)", explainer_output.title or "")
        if match is None:
            return None
        index = int(match.group(1)) - 1
        if index not in explanation:
            return None

        target_names = explanation["metadata"]["target_names"]
        instance = explanation[index]
        predicted_class = instance["predicted_class"]
        predicted_name = target_names[predicted_class]
        predicted_prob = round(instance["model_prediction"][predicted_class], 3)

        return format_story(
            {
                "en": (
                    "The model predicted {predicted_name} "
                    "(p={predicted_prob}). Highlighted regions are those "
                    "whose occlusion most lowered that probability."
                ),
                "es": (
                    "El modelo predijo {predicted_name} "
                    "(p={predicted_prob}). Las regiones resaltadas son "
                    "aquellas cuya oclusión redujo más esa probabilidad."
                ),
                "pt": (
                    "O modelo previu {predicted_name} "
                    "(p={predicted_prob}). As regiões destacadas são "
                    "aquelas cuja oclusão mais reduziu essa probabilidade."
                ),
                "de": (
                    "Das Modell sagte {predicted_name} "
                    "(p={predicted_prob}) voraus. Die hervorgehobenen "
                    "Regionen sind jene, deren Verdeckung diese "
                    "Wahrscheinlichkeit am stärksten verringerte."
                ),
                "zh": (
                    "模型预测为{predicted_name}（p={predicted_prob}）。"
                    "高亮区域是遮挡后该概率下降最多的区域。"
                ),
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
        )
