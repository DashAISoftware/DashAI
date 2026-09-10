import math
from typing import TYPE_CHECKING, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.feature_engineering import (
    FeatureEngineeringConverter,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    float_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Float, Integer

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

OPERATIONS = ["add", "subtract", "multiply", "divide"]


class ColumnArithmeticSchema(BaseSchema):
    """Schema for ColumnArithmetic hyperparameters."""

    operation: schema_field(
        enum_field(OPERATIONS),
        "add",
        description=MultilingualString(
            en=(
                "Arithmetic operation to apply between the selected columns "
                "(or between the single selected column and 'constant')."
            ),
            es=(
                "Operación aritmética a aplicar entre las columnas "
                "seleccionadas (o entre la única columna seleccionada y "
                "'constant')."
            ),
            pt=(
                "Operação aritmética a aplicar entre as colunas selecionadas "
                "(ou entre a única coluna selecionada e 'constant')."
            ),
            de=(
                "Arithmetische Operation zwischen den ausgewählten Spalten "
                "(oder zwischen der einzelnen ausgewählten Spalte und "
                "'constant')."
            ),
            zh="在所选列之间（或在单个所选列与 'constant' 之间）应用的算术运算。",
        ),
    )  # type: ignore
    constant: schema_field(
        none_type(float_field()),
        None,
        description=MultilingualString(
            en=(
                "Fixed number used as the second operand. Only used (and "
                "required) when a single column is selected."
            ),
            es=(
                "Número fijo usado como segundo operando. Solo se usa (y es "
                "requerido) cuando se selecciona una sola columna."
            ),
            pt=(
                "Número fixo usado como segundo operando. Usado (e "
                "necessário) apenas quando uma única coluna é selecionada."
            ),
            de=(
                "Feste Zahl, die als zweiter Operand verwendet wird. Wird nur "
                "verwendet (und benötigt), wenn eine einzelne Spalte "
                "ausgewählt ist."
            ),
            zh="用作第二个操作数的固定数值。仅在选择单个列时使用（且必填）。",
        ),
    )  # type: ignore
    swap_operands: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "When two columns are selected, swap the operand order. By "
                "default the operation is 'first column' OP 'second column' "
                "(in dataset order); enable this to compute 'second' OP "
                "'first' instead. Only affects subtract and divide."
            ),
            es=(
                "Cuando se seleccionan dos columnas, invierte el orden de los "
                "operandos. Por defecto la operación es 'primera columna' OP "
                "'segunda columna' (en el orden del dataset); actívalo para "
                "calcular 'segunda' OP 'primera'. Solo afecta a restar y "
                "dividir."
            ),
            pt=(
                "Quando duas colunas são selecionadas, inverte a ordem dos "
                "operandos. Por padrão a operação é 'primeira coluna' OP "
                "'segunda coluna' (na ordem do dataset); ative para calcular "
                "'segunda' OP 'primeira'. Afeta apenas subtrair e dividir."
            ),
            de=(
                "Wenn zwei Spalten ausgewählt sind, wird die Reihenfolge der "
                "Operanden getauscht. Standardmäßig ist die Operation 'erste "
                "Spalte' OP 'zweite Spalte' (in Datensatzreihenfolge); "
                "aktivieren, um stattdessen 'zweite' OP 'erste' zu berechnen. "
                "Betrifft nur Subtraktion und Division."
            ),
            zh="当选择两列时，交换操作数顺序。默认运算为'第一列' OP '第二列'"
            "（按数据集顺序）；启用此项则改为计算'第二列' OP '第一列'。"
            "仅影响减法和除法。",
        ),
    )  # type: ignore
    output_column_name: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Name of the resulting column. If null, a name is generated "
                "from the operands and the operation."
            ),
            es=(
                "Nombre de la columna resultante. Si es nulo, se genera un "
                "nombre a partir de los operandos y la operación."
            ),
            pt=(
                "Nome da coluna resultante. Se nulo, um nome é gerado a "
                "partir dos operandos e da operação."
            ),
            de=(
                "Name der resultierenden Spalte. Wenn null, wird ein Name "
                "aus den Operanden und der Operation generiert."
            ),
            zh="结果列的名称。如果为空，将根据操作数和运算生成名称。",
        ),
    )  # type: ignore


class ColumnArithmetic(FeatureEngineeringConverter, BaseConverter):
    """Combine the selected columns into a new numeric column.

    Applies addition, subtraction, multiplication, or division element-wise
    to the columns selected in scope. Select **two** columns to operate
    between them, or **one** column to operate between it and a fixed
    ``constant`` (e.g. ``column * 2``). The operands are taken from the
    selection: with two columns the operation is
    ``<first column> <op> <second column>`` in dataset order, which can be
    reversed with ``swap_operands`` (relevant for ``subtract`` and
    ``divide``). Division by zero yields ``NaN`` instead of raising an
    error.

    The original columns are left untouched; the result is appended as a new
    column named ``output_column_name``, or, if not provided,
    ``<column_a>_<operation>_<column_b>`` or ``<column_a>_<operation>_<constant>``.

    The output column is ``Integer`` when both operands are ``Integer`` (a
    whole-number ``constant`` counts as ``Integer``), the operation is
    ``add``, ``subtract``, or ``multiply`` (all of which stay exact on
    integers), and neither operand column has missing values (since a
    missing value has no exact integer representation). ``divide`` always
    produces a ``Float`` column, since integer division is not exact in
    general, and any operation involving a ``Float`` operand, or an
    operand column with missing values, also produces a ``Float`` column.
    """

    SCHEMA = ColumnArithmeticSchema
    DESCRIPTION = MultilingualString(
        en=(
            "Applies an arithmetic operation (add, subtract, multiply, divide) "
            "to the selected columns — two columns to operate between them, or "
            "one column with a fixed constant (e.g. column * 2) — and appends "
            "the result as a new column."
        ),
        es=(
            "Aplica una operación aritmética (sumar, restar, multiplicar, "
            "dividir) a las columnas seleccionadas — dos columnas para operar "
            "entre ellas, o una columna con una constante fija (por ejemplo, "
            "columna * 2) — y agrega el resultado como una nueva columna."
        ),
        pt=(
            "Aplica uma operação aritmética (somar, subtrair, multiplicar, "
            "dividir) às colunas selecionadas — duas colunas para operar "
            "entre elas, ou uma coluna com uma constante fixa (por exemplo, "
            "coluna * 2) — e adiciona o resultado como uma nova coluna."
        ),
        de=(
            "Wendet eine arithmetische Operation (Addieren, Subtrahieren, "
            "Multiplizieren, Dividieren) auf die ausgewählten Spalten an — "
            "zwei Spalten, um zwischen ihnen zu rechnen, oder eine Spalte mit "
            "einer festen Konstante (z. B. Spalte * 2) — und fügt das "
            "Ergebnis als neue Spalte hinzu."
        ),
        zh=(
            "对所选列应用算术运算（加、减、乘、除）——选择两列在其之间运算，"
            "或选择一列与固定常量运算（例如 列 * 2）——并将结果作为新列追加。"
        ),
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Arithmetic combination of the selected columns (or a column and a "
        "constant).",
        es="Combinación aritmética de las columnas seleccionadas (o una "
        "columna y una constante).",
        pt="Combinação aritmética das colunas selecionadas (ou uma coluna e "
        "uma constante).",
        de="Arithmetische Kombination der ausgewählten Spalten (oder einer "
        "Spalte und einer Konstante).",
        zh="对所选列进行算术组合（或一列与一个常量）。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Column Arithmetic",
        es="Aritmética de Columnas",
        pt="Aritmética de Colunas",
        de="Spalten-Arithmetik",
        zh="列算术运算",
    )
    IMAGE_PREVIEW = "column_arithmetic.png"

    metadata = {
        "allowed_types": [Float, Integer],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1, "max": 2},
    }

    def __init__(
        self,
        operation: str,
        constant: Union[float, None] = None,
        swap_operands: bool = False,
        output_column_name: Union[str, None] = None,
    ):
        """Initialise the converter with the operation and options.

        The operand columns are not passed here: they are derived from the
        columns selected in scope during :meth:`fit` (one or two columns).

        Parameters
        ----------
        operation : str
            One of ``"add"``, ``"subtract"``, ``"multiply"``, ``"divide"``.
        constant : float, optional
            Fixed number used as the second operand when a single column is
            selected. Ignored when two columns are selected.
        swap_operands : bool, optional
            When two columns are selected, swap the operand order (compute
            ``second <op> first`` instead of ``first <op> second``). Only
            relevant for ``subtract`` and ``divide``. Defaults to False.
        output_column_name : str, optional
            Name of the resulting column. If ``None`` or not a string, a name
            is generated from the operands and the operation.

        Raises
        ------
        ValueError
            If ``operation`` is not one of the supported values.
        """
        super().__init__()
        if operation not in OPERATIONS:
            raise ValueError(
                f"'operation' must be one of {OPERATIONS}, got '{operation}'."
            )

        self.operation = operation
        self.constant = constant
        self.swap_operands = bool(swap_operands)
        self.output_column_name = (
            output_column_name if isinstance(output_column_name, str) else None
        )
        # Derived during fit() from the columns selected in scope.
        self.operand_b_mode: Union[str, None] = None
        self.column_a: Union[str, None] = None
        self.column_b: Union[str, None] = None
        self._result_column_name: Union[str, None] = None
        self._output_is_integer: bool = False

    @staticmethod
    def _format_constant(value: float) -> str:
        """Render a constant for use in an auto-generated column name."""
        return str(int(value)) if value == int(value) else str(value)

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "ColumnArithmetic":
        """Derive the operands from scope and validate them.

        The operand columns come from the columns selected in scope: two
        columns operate between them (``column_a`` and ``column_b`` in
        dataset order, optionally swapped via ``swap_operands``), one column
        operates against ``constant``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset, expected to contain one or two columns.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        ColumnArithmetic
            The fitted converter instance (self).

        Raises
        ------
        ValueError
            If the number of selected columns is not one or two, if a
            selected column is not numeric (Float or Integer), or if a
            single column is selected without a valid ``constant``.
        """
        columns = list(x.column_names)
        if len(columns) not in (1, 2):
            raise ValueError(
                "ColumnArithmetic requires selecting one or two columns in "
                f"scope, but {len(columns)} were selected."
            )

        for col in columns:
            if not isinstance(x.types.get(col), (Float, Integer)):
                raise ValueError(
                    f"Column '{col}' must be numeric (Float or Integer) to be "
                    "used in ColumnArithmetic."
                )

        if len(columns) == 2:
            self.operand_b_mode = "column"
            first, second = columns
            if self.swap_operands:
                first, second = second, first
            self.column_a = first
            self.column_b = second
            operand_b_label = self.column_b
            operand_b_is_integer = isinstance(x.types.get(self.column_b), Integer)
            has_missing_values = (
                x.arrow_table[self.column_a].null_count > 0
                or x.arrow_table[self.column_b].null_count > 0
            )
        else:
            if not isinstance(self.constant, (int, float)) or isinstance(
                self.constant, bool
            ):
                raise ValueError(
                    "'constant' must be a number when a single column is "
                    "selected in scope."
                )
            if not math.isfinite(self.constant):
                raise ValueError(
                    "'constant' must be a finite number (not NaN or "
                    "infinite) when a single column is selected in scope."
                )
            self.operand_b_mode = "constant"
            self.constant = float(self.constant)
            self.column_a = columns[0]
            self.column_b = None
            operand_b_label = self._format_constant(self.constant)
            operand_b_is_integer = self.constant == int(self.constant)
            has_missing_values = x.arrow_table[self.column_a].null_count > 0

        self._result_column_name = self.output_column_name or (
            f"{self.column_a}_{self.operation}_{operand_b_label}"
        )
        self._output_is_integer = (
            self.operation != "divide"
            and isinstance(x.types.get(self.column_a), Integer)
            and operand_b_is_integer
            and not has_missing_values
        )
        return self

    def _get_operand_b(self, x_pandas, dtype: str):
        """Return the second operand as an array aligned with ``x_pandas``.

        Either the values of ``column_b``, or ``constant`` broadcast to the
        same length, depending on ``operand_b_mode``.
        """
        import numpy as np

        if self.operand_b_mode == "column":
            return x_pandas[self.column_b].to_numpy(dtype=dtype)
        return np.full(len(x_pandas), self.constant, dtype=dtype)

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Compute the arithmetic result and append it as a new column.

        Parameters
        ----------
        x : DashAIDataset
            The dataset containing the operand column(s) derived during
            ``fit``.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        DashAIDataset
            The original dataset with the arithmetic result appended as a
            new column, typed ``Integer`` or ``Float`` depending on the
            operands and the operation (see class docstring).
        """
        import numpy as np
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

        x_pandas = x.to_pandas()

        if self._output_is_integer:
            a = x_pandas[self.column_a].to_numpy(dtype="int64")
            b = self._get_operand_b(x_pandas, "int64")

            if self.operation == "add":
                result = a + b
            elif self.operation == "subtract":
                result = a - b
            else:  # multiply
                result = a * b

            arrow_type = pa.int64()
        else:
            a = x_pandas[self.column_a].to_numpy(dtype="float64")
            b = self._get_operand_b(x_pandas, "float64")

            with np.errstate(divide="ignore", invalid="ignore"):
                if self.operation == "add":
                    result = a + b
                elif self.operation == "subtract":
                    result = a - b
                elif self.operation == "multiply":
                    result = a * b
                else:  # divide
                    result = np.where(b != 0, a / b, np.nan)

            arrow_type = pa.float64()

        new_types = dict(x.types)
        new_types[self._result_column_name] = self.get_output_type()

        return modify_table(
            x,
            {self._result_column_name: pa.array(result, type=arrow_type)},
            types=new_types,
        )

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the output type for the arithmetic result.

        Determined during ``fit``: ``Integer`` when both operands are
        ``Integer`` (a whole-number ``constant`` counts as ``Integer``) and
        the operation isn't ``divide``, ``Float`` otherwise.

        Parameters
        ----------
        column_name : str, optional
            Not used; the result column always has the same type.
            Defaults to None.

        Returns
        -------
        DashAIDataType
            An ``Integer`` type backed by ``pyarrow.int64()``, or a
            ``Float`` type backed by ``pyarrow.float64()``.
        """
        import pyarrow as pa

        if self._output_is_integer:
            return Integer(arrow_type=pa.int64())
        return Float(arrow_type=pa.float64())
