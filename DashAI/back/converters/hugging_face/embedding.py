"""HuggingFace embedding converter with lazy-loaded dependencies."""

from typing import TYPE_CHECKING

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.converters.hugging_face_wrapper import HuggingFaceWrapper
from DashAI.back.core.schema_fields import enum_field, int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class EmbeddingSchema(BaseSchema):
    """Schema for Embedding converter hyperparameters."""

    model_name: schema_field(
        enum_field(
            [
                # Sentence Transformers Models
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
                "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2",
                "sentence-transformers/all-distilroberta-v1",
                # BERT Models
                "bert-base-uncased",
                "bert-large-uncased",
                "bert-base-multilingual-cased",
                "distilbert-base-uncased",
                # RoBERTa Models
                "roberta-base",
                "roberta-large",
                "distilroberta-base",
            ]
        ),
        "sentence-transformers/all-MiniLM-L6-v2",
        description=MultilingualString(
            en="Name of the pretrained model to use",
            es="Nombre del modelo preentrenado a usar",
            pt="Nome do modelo pré-treinado a usar",
            de="Name des vortrainierten Modells, das verwendet werden soll",
            zh="要使用的预训练模型名称",
        ),
    )  # type: ignore

    max_length: schema_field(
        int_field(ge=1),
        512,
        description=MultilingualString(
            en="Maximum sequence length for tokenization",
            es="Longitud máxima de secuencia para la tokenización",
            pt="Comprimento máximo de sequência para a tokenização",
            de="Maximale Sequenzlänge für die Tokenisierung",
            zh="分词的最大序列长度",
        ),
    )  # type: ignore

    batch_size: schema_field(
        int_field(ge=1),
        32,
        description=MultilingualString(
            en="Number of samples to process at once",
            es="Número de muestras a procesar a la vez",
            pt="Número de amostras a processar de uma vez",
            de="Anzahl der gleichzeitig zu verarbeitenden Stichproben",
            zh="每次处理的样本数量",
        ),
    )  # type: ignore

    device: schema_field(
        enum_field(["cuda", "cpu"]),
        "cpu",
        description=MultilingualString(
            en="Device to use for computation",
            es="Dispositivo a usar para el cómputo",
            pt="Dispositivo a usar para o processamento",
            de="Gerät für die Berechnung",
            zh="用于计算的设备",
        ),
    )  # type: ignore

    pooling_strategy: schema_field(
        enum_field(["mean", "cls", "max"]),
        "mean",
        description=MultilingualString(
            en="Strategy to pool token embeddings into sentence embedding",
            es="Estrategia para agrupar embeddings de tokens en uno de oración",
            pt="Estratégia para agregar embeddings de tokens em embedding de sentença",
            de=(
                "Strategie zum Zusammenführen von Token-Einbettungen zu "
                "Satz-Einbettungen"
            ),
            zh="将词元嵌入汇聚为句子嵌入的策略",
        ),
    )  # type: ignore


class Embedding(AdvancedPreprocessingConverter, HuggingFaceWrapper):
    """HuggingFace embedding converter."""

    SCHEMA = EmbeddingSchema
    DESCRIPTION = MultilingualString(
        en="Convert text to embeddings using HuggingFace transformer models.",
        es="Convierte texto a embeddings usando modelos de HuggingFace.",
        pt=(
            "Converte texto em embeddings usando modelos de transformadores "
            "HuggingFace."
        ),
        de=(
            "Text in Einbettungen konvertieren mithilfe von "
            "HuggingFace-Transformermodellen."
        ),
        zh="使用HuggingFace（保留英文）transformer模型将文本转换为嵌入向量。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Embedding", es="Embedding", pt="Embedding", de="Einbettung", zh="嵌入"
    )
    IMAGE_PREVIEW = "embedding.png"

    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialise the embedding converter and extract schema parameters.

        Parameters
        ----------
        **kwargs : dict
            model_name : str, optional
                HuggingFace model ID for the sentence-transformer.
                Default ``"sentence-transformers/all-MiniLM-L6-v2"``.
            pooling_strategy : str, optional
                How to aggregate token embeddings into a sentence vector.
                Default ``"mean"``.
            device : str, optional
                Torch device string (e.g. ``"cpu"`` or ``"cuda:0"``).
                Default ``"cpu"``.
            max_length : int, optional
                Maximum token sequence length. Default ``512``.
            batch_size : int, optional
                Number of examples per inference batch. Default ``32``.
        """
        super().__init__(**kwargs)
        self.pooling_strategy = kwargs.get("pooling_strategy", "mean")
        self.model_name = kwargs.get(
            "model_name", "sentence-transformers/all-MiniLM-L6-v2"
        )
        self.device = kwargs.get("device", "cpu")
        self.max_length = kwargs.get("max_length", 512)
        self.batch_size = kwargs.get("batch_size", 32)
        self.model = None
        self.tokenizer = None

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return ``Float32`` as the output type for all embedding columns.

        Parameters
        ----------
        column_name : str or None, optional
            Name of the output column. Not used, since all embedding columns
            receive the same ``Float32`` type. Default ``None``.

        Returns
        -------
        Float
            A DashAI ``Float`` type backed by ``pyarrow.float32()``.
        """
        import pyarrow as pa

        return Float(arrow_type=pa.float32())

    def _load_model(self):
        """Load the embedding model and tokenizer."""
        from transformers import AutoModel, AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)
        self.model = AutoModel.from_pretrained(self.model_name).to(self.device)
        self.model.eval()

    def _process_batch(self, batch: "DashAIDataset") -> "DashAIDataset":
        """Encode a batch of text columns into dense embedding vectors.

        Each text column is passed through the transformer encoder; the
        mean of the last hidden states is used as the sentence embedding.
        Resulting float32 vectors are stored as separate ``Float`` columns.

        Parameters
        ----------
        batch : DashAIDataset
            A slice of the full dataset. Each column must contain string values.

        Returns
        -------
        DashAIDataset
            Dataset where each original text column is replaced by its
            dense embedding vector column(s).
        """
        import pyarrow as pa
        import torch

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        result_table = batch.arrow_table

        for column in batch.column_names:
            # Get text data from dataset
            texts = [row[column] if row[column] is not None else "" for row in batch]

            # Tokenize
            encoded = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            # Move to device
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**encoded)
                hidden_states = outputs.last_hidden_state

                # Apply pooling strategy
                if self.pooling_strategy == "mean":
                    embeddings = torch.mean(hidden_states, dim=1)
                elif self.pooling_strategy == "cls":
                    embeddings = hidden_states[:, 0]
                else:  # max pooling
                    embeddings = torch.max(hidden_states, dim=1)[0]

            embeddings_np = embeddings.cpu().numpy()

            # Append one column per embedding dimension
            for i in range(embeddings_np.shape[1]):
                result_table = result_table.append_column(
                    f"emb_{column}_{i}",
                    pa.array(embeddings_np[:, i].tolist(), type=pa.float32()),
                )

        # Remove original text columns — they are replaced by their emb_* counterparts
        for column in batch.column_names:
            col_idx = result_table.column_names.index(column)
            result_table = result_table.remove_column(col_idx)

        return DashAIDataset(result_table)
