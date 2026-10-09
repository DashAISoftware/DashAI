"""EfficientNet-B0 image classifier for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import TorchvisionDownloadMixin
from DashAI.back.models.base_torchvision_image_classifier import (
    TorchvisionImageClassifier,
    TorchvisionImageClassifierSchema,
)


class EfficientNetB0ImageClassifier(
    TorchvisionDownloadMixin, TorchvisionImageClassifier
):
    """EfficientNet-B0 image classifier (Tan & Le, 2019).

    Compact baseline of the EfficientNet family, which scales network width,
    depth, and resolution jointly. The classifier head is replaced to match
    the number of target classes. Supports ImageNet pretrained weights.
    """

    SCHEMA = TorchvisionImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="EfficientNet-B0",
        es="EfficientNet-B0",
        pt="EfficientNet-B0",
        de="EfficientNet-B0",
        zh="EfficientNet-B0",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "EfficientNet-B0 (Tan & Le, 2019). Scales network width, depth, "
            "and resolution jointly for the best accuracy/efficiency trade-off. "
            "Smaller and faster than ResNet-18 at similar accuracy."
        ),
        es=(
            "EfficientNet-B0 (Tan & Le, 2019). Escala ancho, profundidad y "
            "resolución de la red de forma conjunta para el mejor balance entre "
            "accuracy y eficiencia. Más pequeño y rápido que ResNet-18."
        ),
        pt=(
            "EfficientNet-B0 (Tan & Le, 2019). Escala largura, profundidade e "
            "resolução da rede de forma conjunta para o melhor equilíbrio entre "
            "acurácia e eficiência. Menor e mais rápido que o ResNet-18."
        ),
        de=(
            "EfficientNet-B0 (Tan & Le, 2019). Skaliert Netzwerkbreite, Tiefe und "
            "Auflösung gemeinsam für das beste Verhältnis zwischen Genauigkeit und "
            "Effizienz. "
            "Kleiner und schneller als ResNet-18 bei vergleichbarer Genauigkeit."
        ),
        zh=(
            "EfficientNet-B0（Tan 和 Le，2019）。联合缩放网络宽度、深度和分辨率，"
            "以实现最佳精度与效率的权衡。在相近精度下比 ResNet-18 更小更快。"
        ),
    )
    COLOR: str = "#00838F"
    ICON: str = "Speed"
    DOWNLOAD_SIZE_BYTES: int = 21_000_000

    @classmethod
    def _weights(cls):
        from torchvision.models import EfficientNet_B0_Weights

        return EfficientNet_B0_Weights.DEFAULT

    def _build_backbone(self, num_classes: int, pretrained: bool):
        import torch.nn as nn
        from torchvision.models import EfficientNet_B0_Weights, efficientnet_b0

        weights = EfficientNet_B0_Weights.DEFAULT if pretrained else None
        with self.local_hub():
            model = efficientnet_b0(weights=weights)
        in_features = model.classifier[1].in_features
        model.classifier = nn.Sequential(
            nn.Dropout(self.dropout_rate),
            nn.Linear(in_features, num_classes),
        )
        return model

    def _classifier_head(self):
        return self.model.classifier
