"""E5 embedding models, which expect ``query:`` and ``passage:`` prefixes."""

from DashAI.back.converters.hugging_face.text_embedding.base import (
    TextEmbeddingConverter,
    same_label,
)
from DashAI.back.core.utils import MultilingualString


class E5TextEmbedding(TextEmbeddingConverter):
    """An E5 model, trained with a prefix naming the role of every text."""

    QUERY_PROMPT = "query: "
    PASSAGE_PROMPT = "passage: "


class MultilingualE5SmallEmbedding(E5TextEmbedding):
    """Multilingual E5, small."""

    MODEL_NAME = "intfloat/multilingual-e5-small"
    DOWNLOAD_SIZE_BYTES = 493308085
    DISPLAY_NAME = same_label("multilingual-e5-small")
    DESCRIPTION = MultilingualString(
        en="Small multilingual retrieval model, good quality for its size.",
        es="Modelo multilingüe pequeño de recuperación, buena calidad para su tamaño.",
        pt="Modelo multilíngue pequeno de recuperação, boa qualidade para o tamanho.",
        de="Kleines mehrsprachiges Retrieval-Modell mit guter Qualität für "
        "seine Größe.",
        zh="小型多语言检索模型，同等规模下质量出色。",
    )


class MultilingualE5BaseEmbedding(E5TextEmbedding):
    """Multilingual E5, base."""

    MODEL_NAME = "intfloat/multilingual-e5-base"
    DOWNLOAD_SIZE_BYTES = 1134536483
    DISPLAY_NAME = same_label("multilingual-e5-base")
    DESCRIPTION = MultilingualString(
        en="Multilingual retrieval model, balanced size and quality.",
        es="Modelo multilingüe de recuperación, equilibrio entre tamaño y calidad.",
        pt="Modelo multilíngue de recuperação, equilíbrio entre tamanho e qualidade.",
        de="Mehrsprachiges Retrieval-Modell mit ausgewogener Größe und Qualität.",
        zh="多语言检索模型，规模与质量均衡。",
    )


class MultilingualE5LargeEmbedding(E5TextEmbedding):
    """Multilingual E5, large."""

    MODEL_NAME = "intfloat/multilingual-e5-large"
    DOWNLOAD_SIZE_BYTES = 2261940460
    DISPLAY_NAME = same_label("multilingual-e5-large")
    DESCRIPTION = MultilingualString(
        en="Best multilingual retrieval quality in this list. Best on a GPU.",
        es="La mejor calidad multilingüe de esta lista. Mejor con GPU.",
        pt="A melhor qualidade multilíngue desta lista. Melhor com GPU.",
        de="Beste mehrsprachige Retrieval-Qualität dieser Liste. Am besten mit GPU.",
        zh="本列表中多语言检索质量最佳，建议使用 GPU。",
    )
