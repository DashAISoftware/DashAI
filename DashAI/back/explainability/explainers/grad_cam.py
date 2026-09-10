import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
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


class GradCamSchema(BaseSchema):
    """Schema for the Grad-CAM explainer hyperparameters.

    Configures the CAM variant used to compute the class activation map.
    """

    method: schema_field(
        enum_field(enum=["gradcam", "gradcam++", "eigencam"]),
        placeholder="gradcam",
        description=MultilingualString(
            en=(
                "CAM variant: 'gradcam' (original), 'gradcam++' (better for "
                "multiple occurrences of a class) or 'eigencam' "
                "(gradient-free, first principal component of activations)."
            ),
            es=(
                "Variante de CAM: 'gradcam' (original), 'gradcam++' (mejor "
                "para múltiples ocurrencias de una clase) o 'eigencam' (sin "
                "gradientes, primera componente principal de activaciones)."
            ),
            pt=(
                "Variante de CAM: 'gradcam' (original), 'gradcam++' (melhor "
                "para múltiplas ocorrências de uma classe) ou 'eigencam' (sem "
                "gradientes, primeira componente principal das ativações)."
            ),
            zh=(
                "CAM变体：'gradcam'（原始）、'gradcam++'（更适合类别多次出现）"
                "或'eigencam'（无梯度，激活的第一主成分）。"
            ),
            de=(
                "CAM-Variante: 'gradcam' (Original), 'gradcam++' (besser bei "
                "mehrfachem Auftreten einer Klasse) oder 'eigencam' "
                "(gradientenfrei, erste Hauptkomponente der Aktivierungen)."
            ),
        ),
        alias=MultilingualString(
            en="CAM method",
            es="Método CAM",
            pt="Método CAM",
            zh="CAM方法",
            de="CAM-Methode",
        ),
    )  # type: ignore


class GradCam(BaseLocalExplainer):
    """Gradient-based class activation maps for image classifiers.

    Grad-CAM backpropagates the score of the predicted class to the last
    convolutional layer and weights its activation maps by the averaged
    gradients, producing a heatmap of the image regions that most influenced
    the prediction. This is a white-box method: it requires a torch module
    with a convolutional backbone, so it works with all DashAI image
    classifiers except the MLP (use Occlusion Saliency there instead).

    Implemented on top of the ``pytorch-grad-cam`` library.

    References
    ----------
    - [1] Selvaraju, R.R. et al. (2017). "Grad-CAM: Visual Explanations from
           Deep Networks via Gradient-based Localization." ICCV 2017.
           https://arxiv.org/abs/1610.02391
    - [2] https://github.com/jacobgil/pytorch-grad-cam
    """

    DISPLAY_NAME = MultilingualString(
        en="Grad-CAM",
        es="Grad-CAM",
        pt="Grad-CAM",
        zh="Grad-CAM",
        de="Grad-CAM",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Highlights the image regions that most influenced the model's "
            "prediction using gradient-weighted class activation maps."
        ),
        es=(
            "Resalta las regiones de la imagen que más influyeron en la "
            "predicción del modelo usando mapas de activación ponderados por "
            "gradientes."
        ),
        pt=(
            "Destaca as regiões da imagem que mais influenciaram a previsão "
            "do modelo usando mapas de ativação ponderados por gradientes."
        ),
        zh="使用梯度加权类激活图突出显示对模型预测影响最大的图像区域。",
        de=(
            "Hebt die Bildregionen hervor, die die Vorhersage des Modells am "
            "stärksten beeinflusst haben, mittels gradientengewichteter "
            "Klassenaktivierungskarten."
        ),
    )
    COLOR = "#C62828"
    SCHEMA = GradCamSchema

    def __init__(self, model: BaseModel, method: str = "gradcam") -> None:
        """Initialize a new instance of a GradCam explainer.

        Parameters
        ----------
        model : BaseModel
            Image classification model to be explained.
        method : str
            CAM variant: 'gradcam', 'gradcam++' or 'eigencam'.
        """
        super().__init__(model)
        self.method = method

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
        GradCam
            The fitted explainer instance (``self``).
        """
        _, y = background_dataset
        self.metadata = {"target_names": get_target_names(self.model, y)}
        return self

    @staticmethod
    def _find_target_layer(module):
        """Return the last Conv2d layer of the module.

        Parameters
        ----------
        module : torch.nn.Module
            The model's torch module.

        Returns
        -------
        torch.nn.Conv2d
            The last convolutional layer.

        Raises
        ------
        ValueError
            If the module has no convolutional layer.
        """
        import torch

        target = None
        for layer in module.modules():
            if isinstance(layer, torch.nn.Conv2d):
                target = layer
        if target is None:
            raise ValueError(
                "Grad-CAM requires a convolutional backbone, but the model "
                "has no Conv2d layer. Use Occlusion Saliency for "
                "non-convolutional image models."
            )
        return target

    def explain_instance(self, instances):
        """Compute a class activation map for each image.

        Parameters
        ----------
        instances : DashAIDataset
            Images to be explained; the first column must contain images.

        Returns
        -------
        dict
            Dictionary with, for each image, the resized image, the CAM
            heatmap and the model prediction.
        """
        import numpy as np
        import torch
        from pytorch_grad_cam import EigenCAM, GradCAM, GradCAMPlusPlus
        from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

        cam_classes = {
            "gradcam": GradCAM,
            "gradcam++": GradCAMPlusPlus,
            "eigencam": EigenCAM,
        }
        cam_class = cam_classes[self.method]

        module = get_torch_module(self.model)
        target_layer = self._find_target_layer(module)
        transform = get_transform(self.model)
        image_size = int(getattr(self.model, "image_size", 224))
        device = getattr(self.model, "device", torch.device("cpu"))

        module = module.to(device).eval()

        explanation = {"metadata": self.metadata}
        with cam_class(model=module, target_layers=[target_layer]) as cam:
            for i, pil_image in enumerate(iter_pil_images(instances)):
                tensor = transform(pil_image).unsqueeze(0).to(device)

                with torch.no_grad():
                    probs = torch.softmax(module(tensor), dim=1)[0]
                predicted_class = int(torch.argmax(probs))

                grayscale = cam(
                    input_tensor=tensor,
                    targets=[ClassifierOutputTarget(predicted_class)],
                )[0]

                resized = pil_image.resize((image_size, image_size))
                explanation[i] = {
                    "image": np.asarray(resized, dtype=np.uint8).tolist(),
                    "heatmap": np.round(grayscale, 4).tolist(),
                    "model_prediction": np.round(
                        probs.detach().cpu().numpy(), 4
                    ).tolist(),
                    "predicted_class": predicted_class,
                }

        return explanation

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Render each image as a heatmap overlay.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group per explained image,
            each holding that image's heatmap overlay.
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
            subtitle = (
                f"{self.method}: regions supporting {predicted_name} "
                f"(p={predicted_prob})"
            )
            overlay = heatmap_overlay_artifact(
                instance["image"], instance["heatmap"], title, subtitle
            )
            groups.append(ArtifactGroup(title=title, artifacts=[overlay]))

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction the heatmap overlay explains.

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
                    "(p={predicted_prob}). Highlighted regions are the "
                    "areas whose activations most supported this class."
                ),
                "es": (
                    "El modelo predijo {predicted_name} "
                    "(p={predicted_prob}). Las regiones resaltadas son las "
                    "áreas cuyas activaciones más respaldaron esta clase."
                ),
                "pt": (
                    "O modelo previu {predicted_name} "
                    "(p={predicted_prob}). As regiões destacadas são as "
                    "áreas cujas ativações mais sustentaram essa classe."
                ),
                "de": (
                    "Das Modell sagte {predicted_name} "
                    "(p={predicted_prob}) voraus. Die hervorgehobenen "
                    "Regionen sind die Bereiche, deren Aktivierungen diese "
                    "Klasse am stärksten unterstützten."
                ),
                "zh": (
                    "模型预测为{predicted_name}（p={predicted_prob}）。"
                    "高亮区域是激活值最支持该类别的区域。"
                ),
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
        )
