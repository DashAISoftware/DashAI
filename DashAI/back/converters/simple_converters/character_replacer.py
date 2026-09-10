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
from DashAI.back.types.value_types import Integer, Text

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
    occurrence of ``char_to_replace`` with ``replacement_char``. If the
    replacement produces a column of pure integers, the column type is promoted
    to ``Integer``.
    """

    SCHEMA = CharacterReplacerSchema
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
            A new dataset with ``char_to_replace`` substituted in all text columns.
            If replacement yields only integer-like values, the column type is
            promoted to ``Integer``.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        if not self._target_columns:
            # if no target columns were set, return the dataset unchanged
            return x

        def try_convert_to_int(value):
            """Try to convert a value to integer, return the original if not possible.

            Parameters
            ----------
            value : object
                The value to convert.

            Returns
            -------
            int or object
                ``int(value)`` on success, or the original ``value`` unchanged
                if a ``ValueError`` or ``TypeError`` is raised.
            """
            try:
                return int(value)
            except (ValueError, TypeError):
                return value

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
                    if isinstance(x.types[column_name], Text):
                        replaced_values = [
                            (
                                val.replace(self.char_to_replace, self.replacement_char)
                                if isinstance(val, str)
                                else val
                            )
                            for val in values
                        ]

                        all_numeric = all(
                            isinstance(val, str) and val.strip().isdigit()
                            for val in replaced_values
                            if isinstance(val, str)
                        )

                        if all_numeric:
                            processed_batch[column_name] = [
                                try_convert_to_int(val) for val in replaced_values
                            ]
                            new_types[column_name] = Integer(arrow_type=pa.int64())
                        else:
                            processed_batch[column_name] = replaced_values
                            new_types[column_name] = Text(arrow_type=pa.string())
                    else:
                        replaced_values = [
                            (
                                val.replace(self.char_to_replace, self.replacement_char)
                                if isinstance(val, str)
                                else val
                            )
                            for val in values
                        ]
                        processed_batch[column_name] = replaced_values
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

        The actual type may be ``Integer`` if all values become numeric during
        ``transform``, but the static default is ``Text``.

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
