"""Shared base of the converters that turn text into dense vectors."""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

import numpy as np

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.converters.hugging_face.pretrained_tool import (
    PretrainedTool,
    device_field,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.utils import DEVICE_PLACEHOLDER
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

PASSAGE = "passage"
QUERY = "query"
ROLES = (PASSAGE, QUERY)
TRUNCATE = "truncate"
AGGREGATE = "aggregate"
SPECIAL_TOKENS = 2


def same_label(text: str) -> MultilingualString:
    """Return a label that reads the same in every language.

    Parameters
    ----------
    text : str
        The label, such as a model name.

    Returns
    -------
    MultilingualString
        ``text`` in every supported language.
    """
    return MultilingualString(en=text, es=text, pt=text, de=text, zh=text)


def token_windows(model: Any, text: str, prompt: Optional[str]) -> List[str]:
    """Split a text into pieces that each fit the model's token limit.

    Parameters
    ----------
    model : SentenceTransformer
        The loaded model, read for ``max_seq_length`` and ``tokenizer``.
    text : str
        The text to split.
    prompt : str, optional
        The prompt prepended to every piece, whose tokens count against the
        limit.

    Returns
    -------
    list of str
        ``[text]`` when it fits or the model has no limit, otherwise the
        decoded token windows in order.
    """
    limit = getattr(model, "max_seq_length", None)
    if not limit:
        return [text]
    tokenizer = model.tokenizer
    prompt_tokens = (
        len(tokenizer(prompt, add_special_tokens=False)["input_ids"]) if prompt else 0
    )
    budget = limit - SPECIAL_TOKENS - prompt_tokens
    ids = tokenizer(text, add_special_tokens=False)["input_ids"]
    if budget < 1 or len(ids) <= budget:
        return [text]
    return [
        tokenizer.decode(ids[start : start + budget])
        for start in range(0, len(ids), budget)
    ]


class TextEmbeddingSchema(BaseSchema):
    """Options shared by every text embedding converter."""

    device: device_field()  # type: ignore
    batch_size: schema_field(
        int_field(ge=1),
        placeholder=32,
        description=MultilingualString(
            en="Number of texts encoded together. Lower it if memory runs out.",
            es="Cantidad de textos codificados juntos. Bájala si falta memoria.",
            pt="Quantidade de textos codificados juntos. Diminua se faltar memória.",
            de="Anzahl gemeinsam kodierter Texte. Verringern, wenn der Speicher "
            "nicht reicht.",
            zh="一次编码的文本数量。内存不足时请调低。",
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Batchgröße",
            zh="批大小",
        ),
    )  # type: ignore
    normalize: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Scale every vector to length one, as cosine similarity expects.",
            es="Escala cada vector a largo uno, como espera la similitud coseno.",
            pt="Escala cada vetor para comprimento um, como a similaridade "
            "cosseno espera.",
            de="Skaliert jeden Vektor auf Länge eins, wie es die "
            "Kosinusähnlichkeit erwartet.",
            zh="将每个向量缩放为单位长度，符合余弦相似度的要求。",
        ),
        alias=MultilingualString(
            en="Normalize",
            es="Normalizar",
            pt="Normalizar",
            de="Normalisieren",
            zh="归一化",
        ),
    )  # type: ignore
    overflow_strategy: schema_field(
        enum_field([TRUNCATE, AGGREGATE]),
        placeholder=TRUNCATE,
        description=MultilingualString(
            en="What to do with a text longer than the model accepts: cut it "
            "(truncate) or encode it in pieces and average them (aggregate).",
            es="Qué hacer con un texto más largo de lo que acepta el modelo: "
            "cortarlo (truncate) o codificarlo por partes y promediarlas "
            "(aggregate).",
            pt="O que fazer com um texto maior do que o modelo aceita: cortá-lo "
            "(truncate) ou codificá-lo em partes e tirar a média (aggregate).",
            de="Was mit einem Text passiert, der länger ist als das Modell "
            "erlaubt: abschneiden (truncate) oder in Teilen kodieren und "
            "mitteln (aggregate).",
            zh="文本超过模型上限时的处理方式：截断（truncate）或分段编码后取平均"
            "（aggregate）。",
        ),
        alias=MultilingualString(
            en="Long texts",
            es="Textos largos",
            pt="Textos longos",
            de="Lange Texte",
            zh="长文本",
        ),
    )  # type: ignore


class TextEmbeddingConverter(AdvancedPreprocessingConverter, PretrainedTool):
    """Encode text into dense vectors with one Sentence Transformers model.

    Each subclass names one Hugging Face checkpoint in ``MODEL_NAME``, so each
    model downloads on its own. Retrievers call :meth:`encode` with a role;
    dataset notebooks call :meth:`transform`, which replaces every text
    column with one float column per dimension, named ``emb_{column}_{i}``.
    """

    SCHEMA = TextEmbeddingSchema
    LEARNS_FROM_DATA = False
    COLUMN_OPERATION = "expand"
    CHANGES_ROW_COUNT = False
    metadata = {"allowed_types": [Text], "allowed_dtypes": []}
    HF_IGNORE_PATTERNS = [*HFDownloadableMixin.HF_IGNORE_PATTERNS, "pytorch_model.bin"]
    QUERY_PROMPT: Optional[str] = None
    PASSAGE_PROMPT: Optional[str] = None

    def __init__(
        self,
        device: str = DEVICE_PLACEHOLDER,
        batch_size: int = 32,
        normalize: bool = True,
        overflow_strategy: str = TRUNCATE,
    ) -> None:
        """Store the encoding options.

        Parameters
        ----------
        device : str, optional
            Device label from :func:`device_field`.
        batch_size : int, optional
            Texts encoded together. Default 32.
        normalize : bool, optional
            Scale vectors to unit length. Default True.
        overflow_strategy : str, optional
            ``"truncate"`` or ``"aggregate"``. Default ``"truncate"``.

        Raises
        ------
        ValueError
            If ``overflow_strategy`` is not supported.
        """
        super().__init__()
        if overflow_strategy not in (TRUNCATE, AGGREGATE):
            raise ValueError(
                f"Unknown overflow strategy '{overflow_strategy}', expected "
                f"'{TRUNCATE}' or '{AGGREGATE}'."
            )
        self.batch_size = batch_size
        self.normalize = normalize
        self.overflow_strategy = overflow_strategy
        self.setup_device(device)
        self.params: Dict[str, Any] = {
            "device": device,
            "batch_size": batch_size,
            "normalize": normalize,
            "overflow_strategy": overflow_strategy,
        }

    def load_pretrained(self, source: str) -> Any:
        """Load the Sentence Transformers model.

        Parameters
        ----------
        source : str
            A local directory or a Hub repo id.

        Returns
        -------
        SentenceTransformer
            The model on the chosen device.
        """
        from sentence_transformers import SentenceTransformer

        return SentenceTransformer(source, device=self.device)

    def prompt(self, role: str) -> Optional[str]:
        """Return the text prepended to inputs of a role.

        Parameters
        ----------
        role : str
            ``"passage"`` or ``"query"``.

        Returns
        -------
        str or None
            The prompt, or None when the model takes the text as is.
        """
        return self.QUERY_PROMPT if role == QUERY else self.PASSAGE_PROMPT

    def encode(self, texts: List[str], role: str = PASSAGE) -> np.ndarray:
        """Encode texts into dense vectors.

        Parameters
        ----------
        texts : list of str
            Texts to encode; None becomes an empty string.
        role : str, optional
            ``"passage"`` for indexed text, ``"query"`` for a search query.

        Returns
        -------
        np.ndarray
            ``(len(texts), dim)`` float32 array.

        Raises
        ------
        ValueError
            If ``role`` is not a known role.
        """
        if role not in ROLES:
            raise ValueError(f"Unknown role '{role}', expected one of {ROLES}.")
        model = self.pretrained()
        values = ["" if text is None else str(text) for text in texts]
        if not values:
            return np.zeros(
                (0, model.get_sentence_embedding_dimension()), dtype=np.float32
            )
        prompt = self.prompt(role)
        if self.overflow_strategy == AGGREGATE:
            return self._encode_aggregated(model, values, prompt)
        return self._encode(model, values, prompt, self.normalize)

    def _encode(
        self, model: Any, texts: List[str], prompt: Optional[str], normalize: bool
    ) -> np.ndarray:
        """Run the model on texts.

        Parameters
        ----------
        model : SentenceTransformer
            The loaded model.
        texts : list of str
            Texts to encode.
        prompt : str, optional
            Prompt prepended by the model.
        normalize : bool
            Whether the model scales vectors to unit length.

        Returns
        -------
        np.ndarray
            ``(len(texts), dim)`` float32 array.
        """
        vectors = model.encode(
            texts,
            batch_size=self.batch_size,
            prompt=prompt,
            normalize_embeddings=normalize,
            convert_to_numpy=True,
            show_progress_bar=False,
        )
        return np.asarray(vectors, dtype=np.float32)

    def _encode_aggregated(
        self, model: Any, texts: List[str], prompt: Optional[str]
    ) -> np.ndarray:
        """Encode each text in token windows and average its windows.

        Parameters
        ----------
        model : SentenceTransformer
            The loaded model.
        texts : list of str
            Texts to encode.
        prompt : str, optional
            Prompt prepended to every window.

        Returns
        -------
        np.ndarray
            ``(len(texts), dim)`` float32 array.
        """
        windows: List[str] = []
        owners: List[int] = []
        for index, text in enumerate(texts):
            pieces = token_windows(model, text, prompt)
            windows.extend(pieces)
            owners.extend([index] * len(pieces))
        vectors = self._encode(model, windows, prompt, False)
        owner_array = np.asarray(owners)
        pooled = np.stack(
            [vectors[owner_array == index].mean(axis=0) for index in range(len(texts))]
        )
        if self.normalize:
            norms = np.linalg.norm(pooled, axis=1, keepdims=True)
            pooled = pooled / np.clip(norms, 1e-12, None)
        return pooled.astype(np.float32)

    def fit(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "TextEmbeddingConverter":
        """Check that every column holds text.

        Parameters
        ----------
        x : DashAIDataset
            The columns to embed.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        TextEmbeddingConverter
            This converter.

        Raises
        ------
        ValueError
            If a column is not a text column.
        """
        for column in x.column_names:
            if not isinstance(x.types.get(column), Text):
                raise ValueError(f"Column {column} must hold text to be embedded.")
        return self

    def transform(
        self, x: "DashAIDataset", y: Optional["DashAIDataset"] = None
    ) -> "DashAIDataset":
        """Replace every text column with its embedding columns.

        Parameters
        ----------
        x : DashAIDataset
            The text columns.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            One float32 column ``emb_{column}_{i}`` per dimension of every
            input column, and no input column.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        table = x.arrow_table
        types: Dict[str, DashAIDataType] = {}
        for column in x.column_names:
            vectors = self.encode(table.column(column).to_pylist(), role=PASSAGE)
            for index in range(vectors.shape[1]):
                name = f"emb_{column}_{index}"
                table = table.append_column(
                    name, pa.array(vectors[:, index], type=pa.float32())
                )
                types[name] = self.get_output_type(name)
        table = table.drop_columns(list(x.column_names))
        return DashAIDataset(table, types=types, splits=x.splits)

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return the type of every embedding column.

        Parameters
        ----------
        column_name : str, optional
            Unused.

        Returns
        -------
        DashAIDataType
            ``Float`` backed by ``pyarrow.float32()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float32())
