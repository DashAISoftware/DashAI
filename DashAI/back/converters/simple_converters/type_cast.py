from typing import TYPE_CHECKING, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer, Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

NEW_TYPES = ["Integer", "Float", "Text", "Categorical"]
ON_ERROR_MODES = ["raise", "skip"]


class TypeCastSchema(BaseSchema):
    """Schema for TypeCast hyperparameters."""

    new_type: schema_field(
        enum_field(NEW_TYPES),
        "Text",
        description=MultilingualString(
            en="Target type to cast the columns in scope to.",
            es="Tipo objetivo al que se convertirán las columnas del alcance.",
            pt="Tipo de destino para o qual as colunas do escopo serão convertidas.",
            de="Zieltyp, in den die Spalten im Geltungsbereich umgewandelt werden.",
            zh="要将范围内的列转换为的目标类型。",
        ),
    )  # type: ignore
    on_error: schema_field(
        enum_field(ON_ERROR_MODES),
        "raise",
        description=MultilingualString(
            en=(
                "What to do when a column cannot be safely converted: 'raise' "
                "to stop with a descriptive error, or 'skip' to leave that "
                "column unchanged and continue with the rest."
            ),
            es=(
                "Qué hacer cuando una columna no puede convertirse de forma "
                "segura: 'raise' para detenerse con un error descriptivo, o "
                "'skip' para dejar esa columna sin cambios y continuar con "
                "el resto."
            ),
            pt=(
                "O que fazer quando uma coluna não pode ser convertida com "
                "segurança: 'raise' para parar com um erro descritivo, ou "
                "'skip' para deixar essa coluna inalterada e continuar com "
                "o restante."
            ),
            de=(
                "Was zu tun ist, wenn eine Spalte nicht sicher konvertiert "
                "werden kann: 'raise', um mit einer aussagekräftigen "
                "Fehlermeldung abzubrechen, oder 'skip', um diese Spalte "
                "unverändert zu lassen und mit dem Rest fortzufahren."
            ),
            zh="当某列无法安全转换时的处理方式：'raise' 以详细错误信息终止，"
            "或 'skip' 保持该列不变并继续处理其余列。",
        ),
    )  # type: ignore


class TypeCast(BasicPreprocessingConverter, BaseConverter):
    """Change the DashAI type of the columns selected in scope.

    Casts every column in scope to ``new_type`` (one of ``"Integer"``,
    ``"Float"``, ``"Text"``, or ``"Categorical"``), reusing the exact same
    validation and conversion rules used when changing column types from
    the dataset upload preview screen (see
    ``DashAI.back.types.type_validation.validate_type_change``, also used by
    the ``/datasets/validate_type_changes`` endpoint). This keeps behaviour
    consistent between the upload preview and pipeline-time type changes.

    Columns already of ``new_type`` are left untouched. If a column's
    values cannot be safely converted (e.g. a ``Text`` column with
    non-numeric values targeting ``Integer``, or a ``Float`` column with
    decimal values targeting ``Integer``), the behaviour is controlled by
    ``on_error``: ``"raise"`` (default) stops with a descriptive,
    column-specific error message, while ``"skip"`` leaves that column
    unchanged, prints a warning, and continues with the rest.
    """

    SCHEMA = TypeCastSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Changes the type of the selected columns (Integer, Float, Text, "
            "or Categorical), using the same validation used in the dataset "
            "upload preview. Columns that cannot be safely converted are "
            "either reported as an error or skipped, depending on 'on_error'."
        ),
        es=(
            "Cambia el tipo de las columnas seleccionadas (Integer, Float, "
            "Text o Categorical), usando la misma validación empleada en la "
            "vista previa de carga del dataset. Las columnas que no pueden "
            "convertirse de forma segura se reportan como error o se omiten, "
            "según 'on_error'."
        ),
        pt=(
            "Altera o tipo das colunas selecionadas (Integer, Float, Text ou "
            "Categorical), usando a mesma validação empregada na pré-"
            "visualização de upload do dataset. Colunas que não podem ser "
            "convertidas com segurança são reportadas como erro ou "
            "ignoradas, dependendo de 'on_error'."
        ),
        de=(
            "Ändert den Typ der ausgewählten Spalten (Integer, Float, Text "
            "oder Categorical) und verwendet dabei dieselbe Validierung wie "
            "in der Upload-Vorschau des Datensatzes. Spalten, die nicht "
            "sicher konvertiert werden können, werden je nach 'on_error' "
            "entweder als Fehler gemeldet oder übersprungen."
        ),
        zh="使用与数据集上传预览相同的验证规则，更改所选列的类型（Integer、"
        "Float、Text 或 Categorical）。无法安全转换的列将根据 'on_error' "
        "报告为错误或被跳过。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Changes the type of the columns in scope.",
        es="Cambia el tipo de las columnas del alcance.",
        pt="Altera o tipo das colunas do escopo.",
        de="Ändert den Typ der Spalten im Geltungsbereich.",
        zh="更改范围内列的类型。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Type Cast",
        es="Cambio de Tipo",
        pt="Conversão de Tipo",
        de="Typumwandlung",
        zh="类型转换",
    )
    IMAGE_PREVIEW = "type_cast.png"

    metadata = {
        "allowed_types": [Integer, Float, Text, Categorical],
        "allowed_dtypes": [],
    }

    def __init__(self, new_type: str, on_error: str = "raise"):
        """Initialise the converter with the target type and error behaviour.

        Parameters
        ----------
        new_type : str
            One of ``"Integer"``, ``"Float"``, ``"Text"``, ``"Categorical"``.
        on_error : str, optional
            Either ``"raise"`` (default), to stop on the first column that
            cannot be converted, or ``"skip"``, to leave it unchanged and
            continue with the rest.

        Raises
        ------
        ValueError
            If ``new_type`` or ``on_error`` is not one of the supported
            values.
        """
        super().__init__()
        if new_type not in NEW_TYPES:
            raise ValueError(
                f"'new_type' must be one of {NEW_TYPES}, got '{new_type}'."
            )
        if on_error not in ON_ERROR_MODES:
            raise ValueError(
                f"'on_error' must be one of {ON_ERROR_MODES}, got '{on_error}'."
            )

        self.new_type = new_type
        self.on_error = on_error
        self._target_columns: list = []
        self._current_types: dict = {}
        self._skip_columns: set = set()
        # Cache of already-converted columns from fit(), reused in transform()
        # when it is called with the same dataset (the common case, since
        # ConverterJob only re-fetches a fresh scope when a row scope is set).
        self._fit_x = None
        self._converted_cache: dict = {}

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "TypeCast":
        """Validate that every column in scope can be cast to ``new_type``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset whose columns will be cast.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        TypeCast
            The fitted converter instance (self).

        Raises
        ------
        ValueError
            If ``on_error`` is ``"raise"`` and a column's values cannot be
            safely converted to ``new_type``.
        """
        from DashAI.back.types.type_validation import validate_type_change

        self._target_columns = list(x.column_names)
        self._current_types = {}
        self._skip_columns = set()
        self._converted_cache = {}
        self._fit_x = x

        if not self._target_columns:
            return self

        x_pandas = x.to_pandas()
        for col in self._target_columns:
            current_type_obj = x.types.get(col)
            if current_type_obj is None:
                print(
                    f"Warning: column '{col}' has no known DashAI type and "
                    "will be left unchanged by TypeCast."
                )
                self._skip_columns.add(col)
                continue

            current_type_str = current_type_obj.to_string().get("type")
            self._current_types[col] = current_type_str

            if current_type_str == self.new_type:
                continue

            is_valid, message, converted = validate_type_change(
                x_pandas[col], current_type_str, self.new_type
            )
            if not is_valid:
                full_message = (
                    f"Column '{col}' cannot be converted from "
                    f"'{current_type_str}' to '{self.new_type}': {message}"
                )
                if self.on_error == "raise":
                    raise ValueError(full_message)
                print(f"Warning: {full_message} The column will be left unchanged.")
                self._skip_columns.add(col)
                continue

            if message:
                print(f"Warning: column '{col}': {message}")
            self._converted_cache[col] = converted

        return self

    def _arrow_type(self):
        """Return the PyArrow type backing ``new_type``."""
        import pyarrow as pa

        return {
            "Integer": pa.int64(),
            "Float": pa.float64(),
            "Text": pa.string(),
            "Categorical": pa.string(),
        }[self.new_type]

    def _cast_values(self, values: list) -> list:
        """Cast a list of non-null-normalised Python values to ``new_type``."""
        if self.new_type == "Integer":
            return [None if v is None else int(v) for v in values]
        if self.new_type == "Float":
            return [None if v is None else float(v) for v in values]
        return [None if v is None else str(v) for v in values]

    def _build_output_type(self, values: list) -> DashAIDataType:
        """Return the DashAI type for a converted column's values."""
        from DashAI.back.types.utils import arrow_to_dashai_types

        if self.new_type != "Categorical":
            return arrow_to_dashai_types(self._arrow_type())
        unique_values = sorted({v for v in values if v is not None})
        return Categorical(values=unique_values)

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Cast the fitted columns to ``new_type``.

        Parameters
        ----------
        x : DashAIDataset
            The dataset whose columns (matching those seen in ``fit``) will
            be cast.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The dataset with the fitted columns cast to ``new_type``.
            Columns that already had ``new_type``, that had no known type,
            or that failed conversion under ``on_error="skip"`` are left
            unchanged.

        Raises
        ------
        ValueError
            If ``on_error`` is ``"raise"`` and a column's values cannot be
            safely converted to ``new_type``.
        """
        import pandas as pd
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table
        from DashAI.back.types.type_validation import validate_type_change

        if not self._target_columns:
            return x

        x_pandas = x.to_pandas()
        new_columns = {}
        new_types = dict(x.types)
        arrow_type = self._arrow_type()
        reuse_cache = x is self._fit_x

        for col in self._target_columns:
            if col in self._skip_columns:
                continue
            current_type_str = self._current_types.get(col)
            if current_type_str == self.new_type:
                continue

            if reuse_cache and col in self._converted_cache:
                converted = self._converted_cache[col]
            else:
                is_valid, message, converted = validate_type_change(
                    x_pandas[col], current_type_str, self.new_type
                )
                if not is_valid:
                    full_message = (
                        f"Column '{col}' cannot be converted from "
                        f"'{current_type_str}' to '{self.new_type}': {message}"
                    )
                    if self.on_error == "raise":
                        raise ValueError(full_message)
                    print(f"Warning: {full_message} The column will be left unchanged.")
                    continue

            clean_values = [
                None if pd.isna(v) else v for v in converted.reindex(x_pandas.index)
            ]
            cast_values = self._cast_values(clean_values)
            new_columns[col] = pa.array(cast_values, type=arrow_type)
            new_types[col] = self._build_output_type(cast_values)

        if not new_columns:
            return x

        return modify_table(x, new_columns, types=new_types)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the output type produced for any column cast by this converter.

        Every column cast by ``transform`` ends up with the same type,
        ``new_type``, regardless of its original type.

        Parameters
        ----------
        column_name : str, optional
            Not used; every cast column has the same output type.
            Defaults to None.

        Returns
        -------
        DashAIDataType
            An ``Integer``, ``Float``, ``Text``, or ``Categorical`` type
            matching ``new_type``. For ``Categorical``, the categories are
            unknown until ``transform`` runs, so an empty placeholder is
            returned.
        """
        from DashAI.back.types.utils import arrow_to_dashai_types

        if self.new_type != "Categorical":
            return arrow_to_dashai_types(self._arrow_type())
        return Categorical(values=[])
