from typing import TYPE_CHECKING, Dict, List, Optional, Tuple, Union

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.converters.category.feature_engineering import (
    FeatureEngineeringConverter,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.preprocessing.structure_types import (
    ColumnItem,
    StateItem,
    StructureDelta,
    type_fields,
)
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.dashai_data_type import DashAIDataType
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class ColumnConcatSchema(BaseSchema):
    """Schema for ColumnConcat hyperparameters."""

    constant: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Fixed string used as the second operand. Only used (and "
                "required) when a single column is selected."
            ),
            es=(
                "String fijo usado como segundo operando. Solo se usa (y es "
                "requerido) cuando se selecciona una sola columna."
            ),
            pt=(
                "String fixa usada como segundo operando. Usada (e "
                "necessária) apenas quando uma única coluna é selecionada."
            ),
            de=(
                "Feste Zeichenkette, die als zweiter Operand verwendet wird. "
                "Wird nur verwendet (und benötigt), wenn eine einzelne Spalte "
                "ausgewählt ist."
            ),
            zh="用作第二个操作数的固定字符串。仅在选择单个列时使用（且必填）。",
        ),
    )  # type: ignore
    separator: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Optional string inserted between the two operands. If null, "
                "they are joined directly with no separator."
            ),
            es=(
                "String opcional insertado entre los dos operandos. Si es "
                "nulo, se unen directamente sin separador."
            ),
            pt=(
                "String opcional inserida entre os dois operandos. Se nula, "
                "são unidos diretamente sem separador."
            ),
            de=(
                "Optionale Zeichenkette, die zwischen die beiden Operanden "
                "eingefügt wird. Wenn null, werden sie direkt ohne "
                "Trennzeichen verbunden."
            ),
            zh="插入在两个操作数之间的可选字符串。如果为空，则直接连接，无分隔符。",
        ),
    )  # type: ignore
    swap_operands: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en=(
                "When two columns are selected, swap the concatenation order. "
                "By default it is 'first column' + 'second column' (in "
                "dataset order); enable this to concatenate 'second' + "
                "'first' instead."
            ),
            es=(
                "Cuando se seleccionan dos columnas, invierte el orden de "
                "concatenación. Por defecto es 'primera columna' + 'segunda "
                "columna' (en el orden del dataset); actívalo para concatenar "
                "'segunda' + 'primera'."
            ),
            pt=(
                "Quando duas colunas são selecionadas, inverte a ordem de "
                "concatenação. Por padrão é 'primeira coluna' + 'segunda "
                "coluna' (na ordem do dataset); ative para concatenar "
                "'segunda' + 'primeira'."
            ),
            de=(
                "Wenn zwei Spalten ausgewählt sind, wird die "
                "Verkettungsreihenfolge getauscht. Standardmäßig ist es "
                "'erste Spalte' + 'zweite Spalte' (in Datensatzreihenfolge); "
                "aktivieren, um stattdessen 'zweite' + 'erste' zu verketten."
            ),
            zh="当选择两列时，交换连接顺序。默认为'第一列' + '第二列'"
            "（按数据集顺序）；启用此项则改为连接'第二列' + '第一列'。",
        ),
    )  # type: ignore
    output_column_name: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Name of the resulting column. If null, a name is generated "
                "from the operands."
            ),
            es=(
                "Nombre de la columna resultante. Si es nulo, se genera un "
                "nombre a partir de los operandos."
            ),
            pt=(
                "Nome da coluna resultante. Se nulo, um nome é gerado a "
                "partir dos operandos."
            ),
            de=(
                "Name der resultierenden Spalte. Wenn null, wird ein Name "
                "aus den Operanden generiert."
            ),
            zh="结果列的名称。如果为空，将根据操作数生成名称。",
        ),
    )  # type: ignore


class ColumnConcat(FeatureEngineeringConverter, BaseConverter):
    """Concatenate the selected string columns into a new column.

    Joins the columns selected in scope element-wise. Select **two** columns
    to concatenate them together, or **one** column to concatenate it with a
    fixed ``constant`` string. With two columns the order is
    ``<first column> + <second column>`` in dataset order, which can be
    reversed with ``swap_operands``. An optional ``separator`` is inserted
    between the operands (none by default, e.g. ``"foo"`` + ``"bar"`` ->
    ``"foobar"``). All selected columns must be ``Text`` or ``Categorical``.
    If either operand is missing (``None``) for a row, the result for that
    row is ``None``.

    The original columns are left untouched; the result is appended as a
    new ``Text`` column named ``output_column_name``, or, if not provided,
    ``<column_a>_concat_<column_b>`` or ``<column_a>_concat_<constant>``.
    """

    SCHEMA = ColumnConcatSchema
    LEARNS_FROM_DATA = False
    DESCRIPTION = MultilingualString(
        en=(
            "Concatenates the selected string columns — two columns to join "
            "them, or one column with a fixed string — with an optional "
            "separator, and appends the result as a new column."
        ),
        es=(
            "Concatena las columnas de texto seleccionadas — dos columnas "
            "para unirlas, o una columna con un string fijo — con un "
            "separador opcional, y agrega el resultado como una nueva "
            "columna."
        ),
        pt=(
            "Concatena as colunas de texto selecionadas — duas colunas para "
            "uni-las, ou uma coluna com uma string fixa — com um separador "
            "opcional, e adiciona o resultado como uma nova coluna."
        ),
        de=(
            "Verkettet die ausgewählten Textspalten — zwei Spalten, um sie "
            "zu verbinden, oder eine Spalte mit einer festen Zeichenkette — "
            "mit einem optionalen Trennzeichen und fügt das Ergebnis als "
            "neue Spalte hinzu."
        ),
        zh="连接所选的文本列——两列将其合并，或一列与固定字符串——带可选分隔符，"
        "并将结果作为新列追加。",
    )
    SHORT_DESCRIPTION = MultilingualString(
        en="Concatenates the selected string columns (or a column and a constant).",
        es="Concatena las columnas de texto seleccionadas (o una columna y "
        "una constante).",
        pt="Concatena as colunas de texto selecionadas (ou uma coluna e uma "
        "constante).",
        de="Verkettet die ausgewählten Textspalten (oder eine Spalte und "
        "eine Konstante).",
        zh="连接所选的文本列（或一列与一个常量）。",
    )
    DISPLAY_NAME = MultilingualString(
        en="Column Concat",
        es="Concatenación de Columnas",
        pt="Concatenação de Colunas",
        de="Spalten-Verkettung",
        zh="列拼接",
    )
    IMAGE_PREVIEW = "column_concat.png"

    metadata = {
        "allowed_types": [Text, Categorical],
        "allowed_dtypes": [],
        "input_cardinality": {"min": 1, "max": 2},
    }

    def __init__(
        self,
        constant: Union[str, None] = None,
        separator: Union[str, None] = None,
        swap_operands: bool = False,
        output_column_name: Union[str, None] = None,
    ):
        """Initialise the converter with the concatenation options.

        The operand columns are not passed here: they are derived from the
        columns selected in scope during :meth:`fit` (one or two columns).

        Parameters
        ----------
        constant : str, optional
            Fixed string used as the second operand when a single column is
            selected. Ignored when two columns are selected.
        separator : str, optional
            String inserted between the two operands. Defaults to None (no
            separator).
        swap_operands : bool, optional
            When two columns are selected, swap the concatenation order
            (``second + first`` instead of ``first + second``). Defaults to
            False.
        output_column_name : str, optional
            Name of the resulting column. If ``None`` or not a string, a name
            is generated from the operands.
        """
        super().__init__()
        self.constant = constant
        self.separator = separator if isinstance(separator, str) else ""
        self.swap_operands = bool(swap_operands)
        self.output_column_name = (
            output_column_name if isinstance(output_column_name, str) else None
        )
        # Derived during fit() from the columns selected in scope.
        self.operand_b_mode: Union[str, None] = None
        self.column_a: Union[str, None] = None
        self.column_b: Union[str, None] = None
        self._result_column_name: Union[str, None] = None

    def fit(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "ColumnConcat":
        """Derive the operands from scope and validate them.

        The operand columns come from the columns selected in scope: two
        columns concatenate together (``column_a`` and ``column_b`` in
        dataset order, optionally swapped via ``swap_operands``), one column
        concatenates with ``constant``.

        Parameters
        ----------
        x : DashAIDataset
            The scoped dataset, expected to contain one or two columns.
        y : DashAIDataset, optional
            Ignored. Defaults to None.

        Returns
        -------
        ColumnConcat
            The fitted converter instance (self).

        Raises
        ------
        ValueError
            If the number of selected columns is not one or two, if a
            selected column is not string-like (Text or Categorical), or if
            a single column is selected without a valid ``constant``.
        """
        types = {name: type(x.types.get(name)).__name__ for name in x.column_names}
        (
            self.operand_b_mode,
            self.column_a,
            self.column_b,
            self._result_column_name,
        ) = self._plan(list(x.column_names), types)
        return self

    def _plan(
        self, columns: List[str], types: Dict[str, str]
    ) -> Tuple[str, str, Optional[str], str]:
        """Work out the operands and the result name from the scope.

        Shared by ``fit`` and ``infer_output_columns``, so the estimated
        column is exactly the one ``transform`` appends.

        Parameters
        ----------
        columns : List[str]
            The scope column names, in dataset order.
        types : Dict[str, str]
            Each scope column's DashAI type name (e.g. "Text").

        Returns
        -------
        tuple
            (operand_b_mode, column_a, column_b, result_column_name);
            column_b is None in "constant" mode.

        Raises
        ------
        ValueError
            If the number of selected columns is not one or two, if a
            selected column is not string-like (Text or Categorical), or if
            a single column is selected without a valid ``constant``.
        """
        if len(columns) not in (1, 2):
            raise ValueError(
                "ColumnConcat requires selecting one or two columns in "
                f"scope, but {len(columns)} were selected."
            )

        for col in columns:
            if types.get(col) not in ("Text", "Categorical"):
                raise ValueError(
                    f"Column '{col}' must be a string (Text or Categorical) "
                    "to be used in ColumnConcat."
                )

        if len(columns) == 2:
            operand_b_mode = "column"
            column_a, column_b = columns
            if self.swap_operands:
                column_a, column_b = column_b, column_a
            operand_b_label = column_b
        else:
            if not isinstance(self.constant, str):
                raise ValueError(
                    "'constant' must be a string when a single column is "
                    "selected in scope."
                )
            operand_b_mode = "constant"
            column_a, column_b = columns[0], None
            operand_b_label = self.constant

        result_column_name = self.output_column_name or (
            f"{column_a}_concat_{operand_b_label}"
        )
        return operand_b_mode, column_a, column_b, result_column_name

    def infer_output_columns(self, inputs: List[StateItem]) -> StructureDelta:
        """Estimate the output: the scope kept, plus the Text result column.

        Parameters
        ----------
        inputs : list of ColumnItem | BlockItem
            The dataset state items in this converter's scope.

        Returns
        -------
        StructureDelta
            The unchanged inputs, plus the single result column.

        Raises
        ------
        ValueError
            If the scope or ``constant`` is invalid (see ``_plan``).
        """
        if not all(isinstance(item, ColumnItem) for item in inputs):
            return super().infer_output_columns(inputs)
        _, _, _, name = self._plan(
            [item.name for item in inputs], {item.name: item.type for item in inputs}
        )
        type_name, dtype = type_fields(self.get_output_type())
        return StructureDelta(
            kept=list(inputs),
            added=[ColumnItem(name=name, type=type_name, dtype=dtype)],
        )

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Concatenate the operands and append the result as a new column.

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
            The original dataset with the concatenated result appended as a
            new ``Text`` column.
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table

        x_pandas = x.to_pandas()

        a = x_pandas[self.column_a].tolist()
        if self.operand_b_mode == "column":
            b = x_pandas[self.column_b].tolist()
        else:
            b = [self.constant] * len(x_pandas)

        sep = self.separator
        result = [
            None if av is None or bv is None else f"{av}{sep}{bv}"
            for av, bv in zip(a, b, strict=True)
        ]

        new_types = dict(x.types)
        new_types[self._result_column_name] = self.get_output_type()

        return modify_table(
            x,
            {self._result_column_name: pa.array(result, type=pa.string())},
            types=new_types,
        )

    def get_output_type(self, column_name: str = None) -> DashAIDataType:
        """Return the output type for the concatenation result.

        Parameters
        ----------
        column_name : str, optional
            Not used; the result column always has the same type.
            Defaults to None.

        Returns
        -------
        DashAIDataType
            A ``Text`` type backed by ``pyarrow.string()``.
        """
        import pyarrow as pa

        return Text(arrow_type=pa.string())
