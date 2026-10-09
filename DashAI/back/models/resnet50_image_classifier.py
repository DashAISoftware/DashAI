"""ResNet-50 image classifier for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import TorchvisionDownloadMixin
from DashAI.back.models.base_torchvision_image_classifier import (
    TorchvisionImageClassifier,
    TorchvisionImageClassifierSchema,
)


class ResNet50ImageClassifier(TorchvisionDownloadMixin, TorchvisionImageClassifier):
    """ResNet-50 image classifier (He et al., 2015).

    50-layer residual network using bottleneck blocks. Deeper and more
    accurate than ResNet-18, and the most-cited CNN variant in the academic
    literature. The final FC layer is replaced to match the target classes.
    Supports ImageNet pretrained weights.
    """

    SCHEMA = TorchvisionImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="ResNet-50",
        es="ResNet-50",
        pt="ResNet-50",
        zh="ResNet-50",
        de="ResNet-50",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "ResNet-50 (He et al., 2015). A 50-layer residual network with "
            "bottleneck blocks and skip connections. The most-cited CNN variant "
            "in academic papers; supports ImageNet pretrained weights."
        ),
        es=(
            "ResNet-50 (He et al., 2015). Red residual de 50 capas con bloques "
            "bottleneck y conexiones de salto. La variante CNN más citada en "
            "papers académicos; soporta pesos preentrenados en ImageNet."
        ),
        pt=(
            "ResNet-50 (He et al., 2015). Rede residual de 50 camadas com blocos "
            "bottleneck e conexões de salto. A variante CNN mais citada em "
            "artigos acadêmicos; suporta pesos prétreinados no ImageNet."
        ),
        zh=(
            "ResNet-50（He 等，2015）。具有瓶颈块和跳跃连接的50层残差网络，"
            "是学术论文中引用最多的卷积神经网络变体；支持 ImageNet 预训练权重。"
        ),
        de=(
            "ResNet-50 (He et al., 2015). Ein residuales Netzwerk mit 50 Schichten, "
            "Bottleneck-Bloecken und Skip-Verbindungen. Die meistzitierte CNN-Variante "
            "in akademischen Publikationen; unterstuetzt ImageNet-vortrainierte "
            "Gewichte."
        ),
    )
    COLOR: str = "#1B5E20"
    ICON: str = "AccountTree"
    DOWNLOAD_SIZE_BYTES: int = 100_000_000

    @classmethod
    def _weights(cls):
        from torchvision.models import ResNet50_Weights

        return ResNet50_Weights.DEFAULT

    def _build_backbone(self, num_classes: int, pretrained: bool):
        import torch.nn as nn
        from torchvision.models import ResNet50_Weights, resnet50

        weights = ResNet50_Weights.DEFAULT if pretrained else None
        with self.local_hub():
            model = resnet50(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(self.dropout_rate),
            nn.Linear(in_features, num_classes),
        )
        return model

    def _classifier_head(self):
        return self.model.fc
