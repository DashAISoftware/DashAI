"""ResNet-18 image classifier for DashAI."""

from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import TorchvisionDownloadMixin
from DashAI.back.models.base_torchvision_image_classifier import (
    TorchvisionImageClassifier,
    TorchvisionImageClassifierSchema,
)


class ResNet18ImageClassifier(TorchvisionDownloadMixin, TorchvisionImageClassifier):
    """ResNet-18 image classifier (He et al., 2015).

    18-layer residual network with skip connections that solve the vanishing
    gradient problem. The final fully-connected layer is replaced to match the
    number of target classes. Supports ImageNet pretrained weights.
    """

    SCHEMA = TorchvisionImageClassifierSchema
    COMPATIBLE_COMPONENTS = ["ImageClassificationTask"]
    DISPLAY_NAME: str = MultilingualString(
        en="ResNet-18",
        es="ResNet-18",
        pt="ResNet-18",
        zh="ResNet-18",
        de="ResNet-18",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "ResNet-18 (He et al., 2015). An 18-layer residual network with "
            "skip connections that enable training very deep networks. "
            "The most-cited CNN in academic literature."
        ),
        es=(
            "ResNet-18 (He et al., 2015). Red residual de 18 capas con "
            "conexiones de salto que permiten entrenar redes muy profundas. "
            "La CNN más citada en la literatura académica."
        ),
        pt=(
            "ResNet-18 (He et al., 2015). Rede residual de 18 camadas com "
            "conexões de salto que permitem treinar redes muito profundas. "
            "A CNN mais citada na literatura acadêmica."
        ),
        zh=(
            "ResNet-18（He 等，2015）。具有跳跃连接的18层残差网络，"
            "可训练非常深的网络。学术文献中引用最多的卷积神经网络。"
        ),
        de=(
            "ResNet-18 (He et al., 2015). Ein 18-schichtiges residuales Netz mit "
            "Skip-Verbindungen, das das Training sehr tiefer Netzwerke ermoglicht. "
            "Das meistzitierte CNN in der akademischen Literatur."
        ),
    )
    COLOR: str = "#2E7D32"
    ICON: str = "AccountTree"
    DOWNLOAD_SIZE_BYTES: int = 47_000_000

    @classmethod
    def _weights(cls):
        from torchvision.models import ResNet18_Weights

        return ResNet18_Weights.DEFAULT

    def _build_backbone(self, num_classes: int, pretrained: bool):
        import torch.nn as nn
        from torchvision.models import ResNet18_Weights, resnet18

        weights = ResNet18_Weights.DEFAULT if pretrained else None
        with self.local_hub():
            model = resnet18(weights=weights)
        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(self.dropout_rate),
            nn.Linear(in_features, num_classes),
        )
        return model

    def _classifier_head(self):
        return self.model.fc
