"""Sentence Transformers embedding models, one converter per checkpoint."""

from DashAI.back.converters.hugging_face.text_embedding.base import (
    TextEmbeddingConverter,
    same_label,
)
from DashAI.back.core.utils import MultilingualString

QWEN3_QUERY_PROMPT = (
    "Instruct: Given a web search query, retrieve relevant passages that answer "
    "the query\nQuery:"
)
HARRIER_QUERY_PROMPT = (
    "Instruct: Given a web search query, retrieve relevant passages that answer "
    "the query\nQuery: "
)


class SentenceTransformerTextEmbedding(TextEmbeddingConverter):
    """A Sentence Transformers model that needs no passage prompt.

    A subclass sets ``QUERY_PROMPT`` when the model was trained with an
    instruction in front of search queries.
    """


class AllMiniLML6V2Embedding(SentenceTransformerTextEmbedding):
    """Fast English sentence embeddings (all-MiniLM-L6-v2)."""

    MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
    DOWNLOAD_SIZE_BYTES = 91632065
    DISPLAY_NAME = same_label("all-MiniLM-L6-v2")
    DESCRIPTION = MultilingualString(
        en="Small, fast English model. A good first choice.",
        es="Modelo inglés pequeño y rápido. Buena primera opción.",
        pt="Modelo inglês pequeno e rápido. Uma boa primeira escolha.",
        de="Kleines, schnelles englisches Modell. Eine gute erste Wahl.",
        zh="小巧快速的英文模型，适合作为首选。",
    )


class AllMpnetBaseV2Embedding(SentenceTransformerTextEmbedding):
    """Higher quality English sentence embeddings (all-mpnet-base-v2)."""

    MODEL_NAME = "sentence-transformers/all-mpnet-base-v2"
    DOWNLOAD_SIZE_BYTES = 438736539
    DISPLAY_NAME = same_label("all-mpnet-base-v2")
    DESCRIPTION = MultilingualString(
        en="English model with better quality than MiniLM, slower.",
        es="Modelo inglés de mejor calidad que MiniLM, más lento.",
        pt="Modelo inglês de melhor qualidade que o MiniLM, mais lento.",
        de="Englisches Modell mit besserer Qualität als MiniLM, langsamer.",
        zh="质量优于 MiniLM 的英文模型，速度较慢。",
    )


class MultiQAMiniLML6CosV1Embedding(SentenceTransformerTextEmbedding):
    """English question to passage retrieval, small (multi-qa-MiniLM-L6-cos-v1)."""

    MODEL_NAME = "sentence-transformers/multi-qa-MiniLM-L6-cos-v1"
    DOWNLOAD_SIZE_BYTES = 91619626
    DISPLAY_NAME = same_label("multi-qa-MiniLM-L6-cos-v1")
    DESCRIPTION = MultilingualString(
        en="Small English model trained to match questions with passages.",
        es="Modelo inglés pequeño entrenado para unir preguntas con pasajes.",
        pt="Modelo inglês pequeno treinado para ligar perguntas a trechos.",
        de="Kleines englisches Modell, trainiert auf Fragen und Textpassagen.",
        zh="针对问题与段落匹配训练的小型英文模型。",
    )


class MultiQAMpnetBaseCosV1Embedding(SentenceTransformerTextEmbedding):
    """English question to passage retrieval (multi-qa-mpnet-base-cos-v1)."""

    MODEL_NAME = "sentence-transformers/multi-qa-mpnet-base-cos-v1"
    DOWNLOAD_SIZE_BYTES = 438721871
    DISPLAY_NAME = same_label("multi-qa-mpnet-base-cos-v1")
    DESCRIPTION = MultilingualString(
        en="English model trained to match questions with passages.",
        es="Modelo inglés entrenado para unir preguntas con pasajes.",
        pt="Modelo inglês treinado para ligar perguntas a trechos.",
        de="Englisches Modell, trainiert auf Fragen und Textpassagen.",
        zh="针对问题与段落匹配训练的英文模型。",
    )


class ParaphraseMultilingualMiniLML12V2Embedding(SentenceTransformerTextEmbedding):
    """Multilingual sentence embeddings, small."""

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    DOWNLOAD_SIZE_BYTES = 499562317
    DISPLAY_NAME = same_label("paraphrase-multilingual-MiniLM-L12-v2")
    DESCRIPTION = MultilingualString(
        en="Small multilingual model covering 50 languages.",
        es="Modelo multilingüe pequeño que cubre 50 idiomas.",
        pt="Modelo multilíngue pequeno que cobre 50 idiomas.",
        de="Kleines mehrsprachiges Modell für 50 Sprachen.",
        zh="覆盖 50 种语言的小型多语言模型。",
    )


class ParaphraseMultilingualMpnetBaseV2Embedding(SentenceTransformerTextEmbedding):
    """Multilingual sentence embeddings, larger."""

    MODEL_NAME = "sentence-transformers/paraphrase-multilingual-mpnet-base-v2"
    DOWNLOAD_SIZE_BYTES = 1126359681
    DISPLAY_NAME = same_label("paraphrase-multilingual-mpnet-base-v2")
    DESCRIPTION = MultilingualString(
        en="Multilingual model covering 50 languages, better than MiniLM.",
        es="Modelo multilingüe de 50 idiomas, mejor que MiniLM.",
        pt="Modelo multilíngue de 50 idiomas, melhor que o MiniLM.",
        de="Mehrsprachiges Modell für 50 Sprachen, besser als MiniLM.",
        zh="覆盖 50 种语言的多语言模型，效果优于 MiniLM。",
    )


class LaBSEEmbedding(SentenceTransformerTextEmbedding):
    """Language agnostic sentence embeddings for 109 languages (LaBSE)."""

    MODEL_NAME = "sentence-transformers/LaBSE"
    DOWNLOAD_SIZE_BYTES = 1903307356
    DISPLAY_NAME = same_label("LaBSE")
    DESCRIPTION = MultilingualString(
        en="Covers 109 languages, strongest at matching translations.",
        es="Cubre 109 idiomas, destaca al unir traducciones.",
        pt="Cobre 109 idiomas, se destaca ao ligar traduções.",
        de="Deckt 109 Sprachen ab, am stärksten beim Finden von Übersetzungen.",
        zh="覆盖 109 种语言，最擅长匹配译文。",
    )


class Qwen3Embedding06B(SentenceTransformerTextEmbedding):
    """Recent multilingual retrieval embeddings (Qwen3-Embedding-0.6B)."""

    MODEL_NAME = "Qwen/Qwen3-Embedding-0.6B"
    DOWNLOAD_SIZE_BYTES = 1207489041
    QUERY_PROMPT = QWEN3_QUERY_PROMPT
    DISPLAY_NAME = same_label("Qwen3-Embedding-0.6B")
    DESCRIPTION = MultilingualString(
        en="Recent multilingual model, strong at retrieval. Best on a GPU.",
        es="Modelo multilingüe reciente, fuerte en recuperación. Mejor con GPU.",
        pt="Modelo multilíngue recente, forte em recuperação. Melhor com GPU.",
        de="Aktuelles mehrsprachiges Modell, stark beim Retrieval. Am besten mit GPU.",
        zh="新近的多语言模型，检索效果出色，建议使用 GPU。",
    )


class HarrierOSS270MEmbedding(SentenceTransformerTextEmbedding):
    """Multilingual retrieval embeddings, small (harrier-oss-v1-270m)."""

    MODEL_NAME = "microsoft/harrier-oss-v1-270m"
    DOWNLOAD_SIZE_BYTES = 570786062
    QUERY_PROMPT = HARRIER_QUERY_PROMPT
    DISPLAY_NAME = same_label("harrier-oss-v1-270m")
    DESCRIPTION = MultilingualString(
        en="Small multilingual retrieval model with long context.",
        es="Modelo multilingüe pequeño de recuperación con contexto largo.",
        pt="Modelo multilíngue pequeno de recuperação com contexto longo.",
        de="Kleines mehrsprachiges Retrieval-Modell mit langem Kontext.",
        zh="支持长上下文的小型多语言检索模型。",
    )


class HarrierOSS06BEmbedding(SentenceTransformerTextEmbedding):
    """Multilingual retrieval embeddings (harrier-oss-v1-0.6b)."""

    MODEL_NAME = "microsoft/harrier-oss-v1-0.6b"
    DOWNLOAD_SIZE_BYTES = 1208039868
    QUERY_PROMPT = HARRIER_QUERY_PROMPT
    DISPLAY_NAME = same_label("harrier-oss-v1-0.6b")
    DESCRIPTION = MultilingualString(
        en="Multilingual retrieval model with long context. Best on a GPU.",
        es="Modelo multilingüe de recuperación con contexto largo. Mejor con GPU.",
        pt="Modelo multilíngue de recuperação com contexto longo. Melhor com GPU.",
        de="Mehrsprachiges Retrieval-Modell mit langem Kontext. Am besten mit GPU.",
        zh="支持长上下文的多语言检索模型，建议使用 GPU。",
    )
