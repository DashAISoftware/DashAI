from typing import TYPE_CHECKING, List, Optional

from pydantic import field_validator

from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.RAG.chunking_models.base_chunking_model import (
    BaseChunkingModel,
)
from DashAI.back.models.RAG.exceptions import RAGChunkingOverlapError


class TokenChunkModelSchema(BaseSchema):
    """Schema for the token-based chunking model configuration."""

    tokenizer_name: schema_field(
        enum_field(
            enum=[
                "intfloat/e5-mistral-7b-instruct",
                "dccuchile/bert-base-spanish-wwm-uncased",
            ],
        ),
        placeholder="intfloat/e5-mistral-7b-instruct",
        alias=MultilingualString(
            en="Tokenizer",
            es="Tokenizador",
            pt="Tokenizador",
            de="Tokenizer",
            zh="分词器",
        ),
        description=MultilingualString(
            en="The tokenizer model used to split the text into tokens.",
            es="El tokenizador que se usa para dividir el texto en tokens.",
            pt="O tokenizador usado para dividir o texto em tokens.",
            de="Das Tokenizer-Modell, das den Text in Tokens zerlegt.",
            zh="用于将文本切分为标记的分词器模型。",
        ),
    )  # type: ignore

    chunk_size: schema_field(
        int_field(gt=1),
        placeholder=400,
        alias=MultilingualString(
            en="Chunk size",
            es="Tamaño de fragmento",
            pt="Tamanho do fragmento",
            de="Chunk-Größe",
            zh="块大小",
        ),
        description=MultilingualString(
            en="Size of each chunk in tokens.",
            es="Tamaño de cada fragmento en tokens.",
            pt="Tamanho de cada fragmento em tokens.",
            de="Größe jedes Chunks in Tokens.",
            zh="每个块的标记数。",
        ),
    )  # type: ignore

    chunk_overlap: schema_field(
        int_field(ge=0),
        placeholder=40,
        alias=MultilingualString(
            en="Chunk overlap",
            es="Superposición entre fragmentos",
            pt="Sobreposição entre fragmentos",
            de="Chunk-Überlappung",
            zh="块重叠",
        ),
        description=MultilingualString(
            en=(
                "Number of tokens to overlap between chunks. "
                "Must be less than the chunk size."
            ),
            es=(
                "Cantidad de tokens que se repiten entre fragmentos "
                "consecutivos. Debe ser menor que el tamaño de fragmento."
            ),
            pt=(
                "Quantidade de tokens repetidos entre fragmentos consecutivos. "
                "Deve ser menor que o tamanho do fragmento."
            ),
            de=(
                "Anzahl der Tokens, die sich zwischen Chunks überlappen. "
                "Muss kleiner als die Chunk-Größe sein."
            ),
            zh="相邻块之间重叠的标记数，必须小于块大小。",
        ),
    )  # type: ignore

    @field_validator("chunk_overlap")
    @classmethod
    def validate_chunk_overlap(cls, v, info):
        """Validate that chunk_overlap is less than chunk_size."""
        chunk_size = info.data.get("chunk_size")
        if chunk_size is not None and v >= chunk_size:
            raise ValueError(
                f"chunk_overlap must be less than chunk_size. "
                f"Got chunk_overlap={v} and chunk_size={chunk_size}"
            )
        return v


if TYPE_CHECKING:
    from transformers import AutoTokenizer


class TokenChunkModel(BaseChunkingModel):
    """Chunking model that splits text into chunks based on token count.

    Uses a HuggingFace ``AutoTokenizer`` to tokenize the text and splits at
    token boundaries with configurable overlap.
    """

    SCHEMA = TokenChunkModelSchema
    CHUNK_UNIT = "tokens"
    DISPLAY_NAME = MultilingualString(
        en="Token chunking",
        es="Fragmentación por tokens",
        pt="Fragmentação por tokens",
        de="Token-basiertes Chunking",
        zh="按标记切分",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Splits documents at token boundaries using a tokenizer, so chunk "
            "sizes line up exactly with the language model's context window. "
            "Slower than character chunking and downloads a tokenizer."
        ),
        es=(
            "Divide los documentos en límites de tokens usando un tokenizador, "
            "de modo que el tamaño de los fragmentos coincide con la ventana "
            "de contexto del modelo. Es más lento que la fragmentación por "
            "caracteres y descarga un tokenizador."
        ),
        pt=(
            "Divide os documentos em limites de tokens usando um tokenizador, "
            "alinhando o tamanho dos fragmentos à janela de contexto do "
            "modelo. É mais lento que a fragmentação por caracteres e baixa "
            "um tokenizador."
        ),
        de=(
            "Teilt Dokumente an Token-Grenzen mit einem Tokenizer, sodass die "
            "Chunk-Größe exakt zum Kontextfenster des Sprachmodells passt. "
            "Langsamer als zeichenbasiertes Chunking und lädt einen Tokenizer."
        ),
        zh=(
            "使用分词器在标记边界切分文档，使块大小与语言模型的"
            "上下文窗口精确对齐。比按字符切分更慢，并且需要下载分词器。"
        ),
    )

    def __init__(self, **kwargs):
        """Initialize the token chunking model.

        Args:
            **kwargs: Must include ``chunk_size``, ``chunk_overlap``, and
                ``tokenizer_name``, plus a ``documents`` mapping passed to
                the parent class.
        """
        # Extract parameters before super().__init__() pops "documents"
        self.chunk_size = kwargs["chunk_size"]
        self.chunk_overlap = kwargs["chunk_overlap"]
        self.tokenizer_name = kwargs["tokenizer_name"]
        self._tokenizer: Optional["AutoTokenizer"] = None
        # self.parameters is set by BaseChunkingModel.validate_and_transform()
        super().__init__(**kwargs)

    @property
    def tokenizer(self) -> "AutoTokenizer":
        """Lazily load and return the HuggingFace tokenizer.

        Returns:
            AutoTokenizer: The tokenizer loaded from the configured
                ``tokenizer_name``.
        """
        if self._tokenizer is None:
            from transformers import AutoTokenizer

            self._tokenizer = AutoTokenizer.from_pretrained(self.tokenizer_name)
        return self._tokenizer

    def chunk_text(self, text: str) -> List[str]:
        """Split text into chunks based on token count.

        Args:
            text: The input text to be chunked.

        Returns:
            List[str]: A list of text chunks, each converted back to a string
                from its constituent tokens.

        Raises:
            RAGChunkingOverlapError: If chunk_overlap is not less than chunk_size.
        """
        if self.chunk_overlap >= self.chunk_size:
            raise RAGChunkingOverlapError(
                f"chunk_overlap ({self.chunk_overlap}) must be less than "
                f"chunk_size ({self.chunk_size})"
            )
        tokens = self.tokenizer.tokenize(text)

        token_chunks = []
        while len(tokens) > 0:
            chunk = tokens[: self.chunk_size]
            token_chunks.append(self.tokenizer.convert_tokens_to_string(chunk))
            tokens = tokens[self.chunk_size - self.chunk_overlap :]

        return token_chunks
