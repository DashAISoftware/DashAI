from typing import TYPE_CHECKING, List, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.core.schema_fields import none_type, schema_field, string_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class CharacterReplacerSchema(BaseSchema):
    """Schema for CharacterReplacer hyperparameters."""

    char_to_replace: schema_field(
        string_field(),
        "",  # default: empty string
        description=MultilingualString(
            en=("The character or substring to be replaced. Cannot be empty."),
            es=("El carácter o subcadena a reemplazar. No puede estar vacío."),
            pt=("O caractere ou substring a ser substituído. Não pode estar vazio."),
            de=(
                "Das zu ersetzende Zeichen oder die Teilzeichenkette. Darf nicht leer "
                "sein."
            ),
            zh="要替换的字符或子字符串。不能为空。",
        ),
    )  # type: ignore
    replacement_char: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "The character or substring to replace with. If null, "
                "'char_to_replace' will be removed."
            ),
            es=(
                "El carácter o subcadena con el que reemplazar. Si es nulo, "
                "se eliminará 'char_to_replace'.",
            ),
            pt=(
                "O caractere ou substring com o qual substituir. Se nulo, "
                "'char_to_replace' será removido."
            ),
            de=(
                "Das Ersatzzeichen oder die Ersatzteilzeichenkette. Wenn null, "
                "wird 'char_to_replace' entfernt."
            ),
            zh="用于替换的字符或子字符串。如果为空，则删除'char_to_replace'。",
        ),
    )  # type: ignore


class CharacterReplacer(BasicPreprocessingConverter, BaseConverter):
    """Replace or remove a character or substring in all selected text columns.

    Scans each value in the configured string columns and substitutes every
    occurrence of ``char_to_replace`` with ``replacement_char``. Every column
    keeps its type, even when the replacement leaves only digits: follow up
    with TypeCast to turn such a column into ``Integer``. Deciding that from
    the values would make the output type depend on the data (and on each
    batch), so it could not be known before fitting.
    """

    SCHEMA = CharacterReplacerSchema
    LEARNS_FROM_DATA = False
    PRESERVES_INPUT_TYPE = True
    DESCRIPTION = MultilingualString(
        en=(
            "Replaces or removes specified characters/substrings in selected "
            "string columns."
        ),
        es=(
            "Reemplaza o elimina caracteres/subcadenas especificados en las "
            "columnas de texto seleccionadas."
        ),
        pt=(
            "Substitui ou remove caracteres/substrings especificados nas "
            "colunas de texto selecionadas."
        ),
        de=(
            "Ersetzt oder entfernt angegebene Zeichen/Teilzeichenketten in "
            "ausgewählten Text-Spalten."
        ),
        zh="替换或删除所选字符串列中指定的字符/子字符串。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Character Replacer",
        es="Reemplazador de Caracteres",
        pt="Substituidor de Caracteres",
        de="Zeichenersetzung",
        zh="字符替换器",
    )
    IMAGE_PREVIEW = "character_replacer.png"

    metadata = {
        "allowed_types": [Text, Categorical],
        "allowed_dtypes": [],
    }

    def __init__(self, char_to_replace: str, replacement_char: str):
        """Initialise the character replacer with the target and replacement characters.

        Parameters
        ----------
        char_to_replace : str
            The character to search for in text columns.  Must be non-empty.
        replacement_char : str or None
            The character to substitute in.  ``None`` or non-string values are
            normalised to an empty string (effectively deleting the character).

        Raises
        ------
        ValueError
            If ``char_to_replace`` is empty or not a string.
        """
        super().__init__()
        if not isinstance(char_to_replace, str) or not char_to_replace:
            raise ValueError("'char_to_replace' must be a non-empty string.")

        self.char_to_replace = char_to_replace
        if replacement_char is None or not isinstance(replacement_char, str):
            replacement_char = ""
        self.replacement_char = replacement_char
        self._target_columns: List[str] = []

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "CharacterReplacer":
        """Identify which columns in ``x`` are of Text type.

        Parameters
        ----------
        x : DashAIDataset
            The dataset whose columns will be inspected.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        CharacterReplacer
            The fitted converter instance (self).
        """
        self._target_columns = []
        if not x.column_names:
            return self

        for col_name in x.column_names:
            if col_name in x.types and isinstance(
                x.types[col_name], (Text, Categorical)
            ):
                self._target_columns.append(col_name)
            else:
                print(
                    f"Warning: Column '{col_name}' in scope is not of "
                    "Text or Categorical type "
                    "and will be ignored by CharacterReplacer."
                )
        if not self._target_columns:
            print(
                "Warning: CharacterReplacer did not find any valid "
                "Text or Categorical columns "
                "in the provided scope."
            )
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Apply the character replacement to the fitted text columns.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            A new dataset with ``char_to_replace`` substituted in all text
            columns, each keeping its type.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if not self._target_columns:
            # if no target columns were set, return the dataset unchanged
            return x

        new_types = x.types.copy()
        categorical_new_values: dict = {
            col: set()
            for col in self._target_columns
            if isinstance(x.types[col], Categorical)
        }

        def replace_function(batch):
            """Apply character replacement to each column in a HuggingFace batch."""
            processed_batch = {}
            for column_name, values in batch.items():
                if column_name in self._target_columns:
                    replaced_values = [
                        (
                            val.replace(self.char_to_replace, self.replacement_char)
                            if isinstance(val, str)
                            else val
                        )
                        for val in values
                    ]
                    processed_batch[column_name] = replaced_values
                    if column_name in categorical_new_values:
                        categorical_new_values[column_name].update(
                            v for v in replaced_values if v is not None
                        )
                else:
                    processed_batch[column_name] = values
            return processed_batch

        transformed_hf_dataset = x.map(replace_function, batched=True)

        for col_name, new_values in categorical_new_values.items():
            old_cat = x.types[col_name]
            new_types[col_name] = Categorical(
                values=sorted(new_values),
                dtype=old_cat.dtype,
                converted=old_cat.converted,
            )

        return DashAIDataset(
            transformed_hf_dataset.data.table,
            types=new_types,
            splits=x.splits,
        )

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the default output type for a transformed column.

        A transformed column keeps its own input type (``Text`` or
        ``Categorical``); ``Text`` is only the default with no column given.

        Parameters
        ----------
        column_name : str, optional
            Not used. Defaults to None.

        Returns
        -------
        DashAIDataType
            A Text type backed by ``pyarrow.string()``.
        """
        import pyarrow as pa

        return Text(arrow_type=pa.string())
