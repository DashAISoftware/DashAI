from typing import TYPE_CHECKING, Optional

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.converters.hugging_face_wrapper import HuggingFaceWrapper
from DashAI.back.core.schema_fields import enum_field, int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Integer, Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TokenizerSchema(BaseSchema):
    """Schema for TokenizerConverter hyperparameters."""

    model_name: schema_field(
        enum_field(
            [
                "bert-base-uncased",
                "bert-large-uncased",
                "distilbert-base-uncased",
                "roberta-base",
                "roberta-large",
                "distilroberta-base",
                "sentence-transformers/all-MiniLM-L6-v2",
                "sentence-transformers/all-mpnet-base-v2",
            ]
        ),
        "bert-base-uncased",
        description=MultilingualString(
            en="Name of the pretrained tokenizer model",
            es="Nombre del modelo de tokenización preentrenado",
            pt="Nome do modelo de tokenizer pré-treinado",
            de="Name des vortrainierten Tokenizer-Modells",
            zh="预训练分词器模型的名称",
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


class TokenizerConverter(AdvancedPreprocessingConverter, HuggingFaceWrapper):
    """Converter that tokenizes text and stores each token ID in a separate column."""

    SCHEMA = TokenizerSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Tokenize text into input IDs; each token ID goes into its own column. "
            "Attention mask is ignored."
        ),
        es=(
            "Tokeniza texto a IDs de entrada; cada ID va en su propia columna. "
            "Se ignora la máscara de atención."
        ),
        pt=(
            "Tokeniza texto em IDs de entrada; cada ID de token vai para sua própria "
            "coluna. A máscara de atenção é ignorada."
        ),
        de=(
            "Text in Eingabe-IDs tokenisieren; jede Token-ID geht in ihre eigene "
            "Spalte. "
            "Die Aufmerksamkeitsmaske wird ignoriert."
        ),
        zh=("将文本分词为输入ID；每个词元ID存入独立列。注意力掩码被忽略。"),
    )
    DISPLAY_NAME = MultilingualString(
        en="Tokenizer", es="Tokenizador", pt="Tokenizer", de="Tokenisierer", zh="分词器"
    )
    IMAGE_PREVIEW = "tokenizer.png"

    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
    }

    def __init__(self, **kwargs):
        """Initialise the tokenizer converter and extract schema parameters.

        Parameters
        ----------
        **kwargs : dict
            model_name : str, optional
                HuggingFace tokenizer model ID.
                Default ``"bert-base-uncased"``.
            device : str, optional
                Torch device string. Default ``"cpu"``.
            max_length : int, optional
                Maximum token sequence length. Default ``512``.
            batch_size : int, optional
                Number of examples per inference batch. Default ``32``.
        """
        super().__init__(**kwargs)
        self.model_name = kwargs.get("model_name", "bert-base-uncased")
        self.device = kwargs.get("device", "cpu")
        self.max_length = kwargs.get("max_length", 512)
        self.batch_size = kwargs.get("batch_size", 32)
        self.tokenizer = None

    def _load_model(self):
        """Load tokenizer only."""
        from transformers import AutoTokenizer

        self.tokenizer = AutoTokenizer.from_pretrained(self.model_name)

    def _process_batch(self, batch: "DashAIDataset") -> "DashAIDataset":
        """Tokenise a batch of text columns and store token IDs as integer columns.

        Each text column is tokenised with the loaded HuggingFace tokenizer.
        The resulting token-id sequence for each column is stored as a new
        ``Integer``-typed column whose name matches the source column.

        Parameters
        ----------
        batch : DashAIDataset
            A slice of the full dataset. Each column must contain string values.

        Returns
        -------
        DashAIDataset
            Dataset where each original text column is replaced by its
            token-ID list column.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        result_table = batch.arrow_table

        for column in batch.column_names:
            texts = [row[column] for row in batch]

            encoded = self.tokenizer(
                texts,
                padding=True,
                truncation=True,
                max_length=self.max_length,
                return_tensors="pt",
            )

            # Move tensor to the specified device
            input_ids = encoded["input_ids"].to(self.device)

            # Append one column per token position
            for i in range(input_ids.size(1)):
                result_table = result_table.append_column(
                    f"tok_{column}_{i}",
                    pa.array(input_ids[:, i].tolist(), type=pa.int64()),
                )

        # Remove original text columns — they are replaced by their tok_* counterparts
        for column in batch.column_names:
            col_idx = result_table.column_names.index(column)
            result_table = result_table.remove_column(col_idx)

        return DashAIDataset(result_table)

    def get_output_type(self, column_name: Optional[str] = None) -> DashAIDataType:
        """Return the DashAI data type produced by this converter for a column.

        The output of this converter is a set of integer columns, one per
        token position. The number of output columns depends on the maximum
        sequence length specified in the configuration.

        Parameters
        ----------
        column_name : str, optional
            The column name to look up in the fitted encoders. When provided
            and the encoder has been fitted, the returned type reflects the
            actual fitted classes. Defaults to None.

        Returns
        -------
        DashAIDataType
            An Integer type for each token position column.
        """
        import pyarrow as pa

        return Integer(arrow_type=pa.int64())
