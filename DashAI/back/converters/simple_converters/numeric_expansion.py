from typing import TYPE_CHECKING, Dict, List, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.feature_engineering import (
    FeatureEngineeringConverter,
)
from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

OPERATIONS = ["log1p", "square", "sqrt"]


class NumericExpansionSchema(BaseSchema):
    """Schema for NumericExpansion hyperparameters."""

    operation: schema_field(
        enum_field(OPERATIONS),
        "log1p",
        description=MultilingualString(
            en=(
                "Unary numeric expansion to apply to each selected column: "
                "'log1p' (ln(1+x)), 'square' (x^2), or 'sqrt' (sqrt(x))."
            ),
            es=(
                "Expansión numérica unaria a aplicar a cada columna "
                "seleccionada: 'log1p' (ln(1+x)), 'square' (x^2) o "
                "'sqrt' (raíz cuadrada de x)."
            ),
            pt=(
                "Expansão numérica unária a aplicar a cada coluna "
                "selecionada: 'log1p' (ln(1+x)), 'square' (x^2) ou "
                "'sqrt' (raiz quadrada de x)."
            ),
            de=(
                "Unäre numerische Erweiterung, die auf jede ausgewählte "
                "Spalte angewendet wird: 'log1p' (ln(1+x)), 'square' (x^2) "
                "oder 'sqrt' (Quadratwurzel von x)."
            ),
            zh="应用于每个所选列的一元数值扩展："
            "'log1p'（ln(1+x)）、'square'（x^2）或 'sqrt'（x 的平方根）。",
        ),
    )  # type: ignore


class NumericExpansion(FeatureEngineeringConverter, BaseConverter):
    """Derive a new numeric feature from each selected column via a unary function.

    Applies one of ``log1p`` (``ln(1+x)``), ``square`` (``x^2``), or ``sqrt``
    (``sqrt(x)``) to every numeric column in scope, appending one new column
    per input column named ``<operation>_<column>``. Values outside the
    domain of the chosen function (``x <= -1`` for ``log1p``, ``x < 0`` for
    ``sqrt``) become ``NaN`` in the corresponding output.

    The original columns are left untouched. ``square`` preserves the input
    column's type (``Integer`` stays ``Integer``, ``Float`` stays ``Float``)
    when the source column has no missing values, since squaring is exact
    for both. ``log1p`` and ``sqrt`` always produce a ``Float`` column, since
    they can yield non-integer or ``NaN`` results even from integer input,
    and ``square`` also falls back to ``Float`` when the source ``Integer``
    column has missing values (since a missing value has no exact integer
    representation).
    """

    SCHEMA = NumericExpansionSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Applies a unary numeric expansion (log1p, square, or sqrt) to "
            "each selected column and appends the result as a new column."
        ),
        es=(
            "Aplica una expansión numérica unaria (log1p, square o sqrt) a "
            "cada columna seleccionada y agrega el resultado como una nueva "
            "columna."
        ),
        pt=(
            "Aplica uma expansão numérica unária (log1p, square ou sqrt) a "
            "cada coluna selecionada e adiciona o resultado como uma nova "
            "coluna."
        ),
        de=(
            "Wendet eine unäre numerische Erweiterung (log1p, square oder "
            "sqrt) auf jede ausgewählte Spalte an und fügt das Ergebnis als "
            "neue Spalte hinzu."
        ),
        zh=(
            "对每个所选列应用一元数值扩展（log1p、square 或 sqrt），"
            "并将结果作为新列追加。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Unary numeric expansion (log1p, square, sqrt) of a column.",
        es="Expansión numérica unaria (log1p, square, sqrt) de una columna.",
        pt="Expansão numérica unária (log1p, square, sqrt) de uma coluna.",
        de="Unäre numerische Erweiterung (log1p, square, sqrt) einer Spalte.",
        zh="列的一元数值扩展（log1p、square、sqrt）。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Numeric Expansion",
        es="Expansión Numérica",
        pt="Expansão Numérica",
        de="Numerische Erweiterung",
        zh="数值扩展",
    )
    IMAGE_PREVIEW = "numeric_expansion.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
    }

    def __init__(self, operation: str):
        """Initialise the converter with the unary operation to apply.

        Parameters
        ----------
        operation : str
            One of ``"log1p"``, ``"square"``, ``"sqrt"``.

        Raises
        ------
        ValueError
            If ``operation`` is not one of the supported operations.
        """
        super().__init__()
        if operation not in OPERATIONS:
            raise ValueError(
                f"'operation' must be one of {OPERATIONS}, got '{operation}'."
            )
        self.operation = operation
        self._target_columns: List[str] = []
        self._output_types: Dict[str, DashAIDataType] = {}

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "NumericExpansion":
        """Identify which columns in ``x`` are numeric (Float or Integer).

        Also precomputes the output type of each resulting column: ``square``
        keeps the input column's type, while ``log1p`` and ``sqrt`` always
        produce ``Float``.

        Parameters
        ----------
        x : DashAIDataset
            The dataset whose columns will be inspected.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        NumericExpansion
            The fitted converter instance (self).
        """
        import pyarrow as pa

        self._target_columns = []
        self._output_types = {}
        for col_name in x.column_names:
            col_type = x.types.get(col_name)
            if isinstance(col_type, (Float, Integer)):
                self._target_columns.append(col_name)
                new_col_name = f"{self.operation}_{col_name}"
                has_missing_values = x.arrow_table[col_name].null_count > 0
                if (
                    self.operation == "square"
                    and isinstance(col_type, Integer)
                    and not has_missing_values
                ):
                    self._output_types[new_col_name] = Integer(arrow_type=pa.int64())
                else:
                    self._output_types[new_col_name] = Float(arrow_type=pa.float64())
            else:
                print(
                    f"Warning: Column '{col_name}' in scope is not numeric "
                    "(Float or Integer) and will be ignored by NumericExpansion."
                )
        if not self._target_columns:
            print(
                "Warning: NumericExpansion did not find any valid numeric "
                "columns in the provided scope."
            )
        return self

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Apply the configured unary expansion to the fitted numeric columns.

        Parameters
        ----------
        x : DashAIDataset
            The dataset to transform.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The dataset with one new ``<operation>_<column>`` column appended
            per fitted numeric column, typed ``Integer`` or ``Float``
            depending on the source column and the operation (see class
            docstring).
        """
        import numpy as np
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

        if not self._target_columns:
            return x

        x_pandas = x.to_pandas()
        new_columns = {}
        new_types = dict(x.types)

        with np.errstate(divide="ignore", invalid="ignore"):
            for col in self._target_columns:
                new_col_name = f"{self.operation}_{col}"
                output_type = self._output_types[new_col_name]

                if isinstance(output_type, Integer):
                    values = x_pandas[col].to_numpy(dtype="int64")
                    result = values**2
                    arrow_type = pa.int64()
                else:
                    values = x_pandas[col].to_numpy(dtype="float64")
                    if self.operation == "log1p":
                        result = np.where(values > -1, np.log1p(values), np.nan)
                    elif self.operation == "square":
                        result = values**2
                    else:  # sqrt
                        result = np.where(values >= 0, np.sqrt(values), np.nan)
                    arrow_type = pa.float64()

                new_columns[new_col_name] = pa.array(result, type=arrow_type)
                new_types[new_col_name] = output_type

        return modify_table(x, new_columns, types=new_types)

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the output type for a given expanded column.

        Determined during ``fit``: ``Integer`` when the operation is
        ``square`` and the source column is ``Integer``, ``Float``
        otherwise.

        Parameters
        ----------
        column_name : str, optional
            Name of the output column (e.g. ``"square_age"``). Defaults to
            None.

        Returns
        -------
        DashAIDataType
            An ``Integer`` type backed by ``pyarrow.int64()``, or a
            ``Float`` type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        if column_name in self._output_types:
            return self._output_types[column_name]
        return Float(arrow_type=pa.float64())
