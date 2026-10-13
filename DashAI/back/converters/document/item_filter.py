"""Drop document items by a rule."""

import re
from typing import TYPE_CHECKING, Optional, Union

from DashAI.back.converters.category.document_processing import (
    DocumentProcessingConverter,
)
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.core.schema_fields import (
    enum_field,
    int_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

EVERY_ITEM = "Every selected item"
BY_LENGTH = "Too short or too long"
MATCHING = "Matching the pattern"
NOT_MATCHING = "Not matching the pattern"
RULES = [BY_LENGTH, MATCHING, NOT_MATCHING, EVERY_ITEM]


class DocumentItemFilterSchema(BaseSchema):
    """Schema for the document item filter."""

    rule: schema_field(
        enum_field(RULES),
        BY_LENGTH,
        description=MultilingualString(
            en=(
                "Which selected items to drop. 'Every selected item' drops the "
                "whole scope, for example the page headers and footers; it is "
                "the only rule for Image items."
            ),
            es=(
                "Qué elementos seleccionados eliminar. 'Every selected item' "
                "elimina todo el alcance, por ejemplo los encabezados y pies de "
                "página; es la única regla para elementos Image."
            ),
            pt=(
                "Quais itens selecionados remover. 'Every selected item' remove "
                "todo o escopo, por exemplo cabeçalhos e rodapés de página; é a "
                "única regra para itens Image."
            ),
            de=(
                "Welche ausgewählten Elemente entfernt werden. 'Every selected "
                "item' entfernt den ganzen Bereich, etwa Kopf und Fußzeilen; für "
                "Image Elemente ist es die einzige Regel."
            ),
            zh=(
                "要删除哪些所选元素。'Every selected item' 删除整个范围，"
                "例如页眉和页脚；这是 Image 元素唯一可用的规则。"
            ),
        ),
        alias=MultilingualString(
            en="Drop",
            es="Eliminar",
            pt="Remover",
            de="Entfernen",
            zh="删除",
        ),
    )  # type: ignore
    min_characters: schema_field(
        int_field(ge=0),
        1,
        description=MultilingualString(
            en=(
                "With 'Too short or too long', items with fewer characters, "
                "not counting surrounding spaces, are dropped."
            ),
            es=(
                "Con 'Too short or too long', se eliminan los elementos con menos "
                "caracteres, sin contar los espacios de los extremos."
            ),
            pt=(
                "Com 'Too short or too long', itens com menos caracteres, sem "
                "contar os espaços das bordas, são removidos."
            ),
            de=(
                "Bei 'Too short or too long' werden Elemente mit weniger Zeichen, "
                "ohne Leerraum am Rand, entfernt."
            ),
            zh=(
                "使用 'Too short or too long' 时，删除字符数（不含首尾空白）少于此值的"
                "元素。"
            ),
        ),
        alias=MultilingualString(
            en="Minimum characters",
            es="Mínimo de caracteres",
            pt="Mínimo de caracteres",
            de="Mindestanzahl Zeichen",
            zh="最少字符数",
        ),
    )  # type: ignore
    max_characters: schema_field(
        none_type(int_field(ge=1)),
        None,
        description=MultilingualString(
            en=(
                "With 'Too short or too long', items with more characters are "
                "dropped. Empty means no upper limit."
            ),
            es=(
                "Con 'Too short or too long', se eliminan los elementos con más "
                "caracteres. Vacío significa sin límite superior."
            ),
            pt=(
                "Com 'Too short or too long', itens com mais caracteres são "
                "removidos. Vazio significa sem limite superior."
            ),
            de=(
                "Bei 'Too short or too long' werden Elemente mit mehr Zeichen "
                "entfernt. Leer bedeutet keine Obergrenze."
            ),
            zh=(
                "使用 'Too short or too long' 时，删除字符数多于此值的元素。为空表示无"
                "上限。"
            ),
        ),
        alias=MultilingualString(
            en="Maximum characters",
            es="Máximo de caracteres",
            pt="Máximo de caracteres",
            de="Höchstanzahl Zeichen",
            zh="最多字符数",
        ),
    )  # type: ignore
    pattern: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Regular expression (Python syntax) searched in each item by the "
                "pattern rules, such as '^Page \\d+$'."
            ),
            es=(
                "Expresión regular (sintaxis de Python) que buscan las reglas de "
                "patrón en cada elemento, como '^Page \\d+$'."
            ),
            pt=(
                "Expressão regular (sintaxe Python) procurada em cada item pelas "
                "regras de padrão, como '^Page \\d+$'."
            ),
            de=(
                "Regulärer Ausdruck (Python Syntax), den die Musterregeln in "
                "jedem Element suchen, etwa '^Page \\d+$'."
            ),
            zh=(
                "模式规则在每个元素中搜索的正则表达式（Python 语法），例如 '^Page "
                "\\d+$'。"
            ),
        ),
        alias=MultilingualString(
            en="Pattern",
            es="Patrón",
            pt="Padrão",
            de="Muster",
            zh="模式",
        ),
    )  # type: ignore


class DocumentItemFilter(DocumentProcessingConverter, DocumentConverter):
    """Drop the selected document items that a rule picks.

    The rule drops items that are too short or too long, items that match or
    do not match a regular expression, or every selected item, which is how
    page headers, footers or other kinds are removed.
    """

    SCHEMA = DocumentItemFilterSchema
    DISPLAY_NAME = MultilingualString(
        en="Item Filter",
        es="Filtro de Elementos",
        pt="Filtro de Itens",
        de="Elementfilter",
        zh="元素过滤器",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Drops document items that are too short or too long, that match a "
            "pattern, or every selected item, such as page headers."
        ),
        es=(
            "Elimina elementos del documento demasiado cortos o largos, que "
            "coinciden con un patrón, o todos los seleccionados, como los "
            "encabezados de página."
        ),
        pt=(
            "Remove itens do documento curtos ou longos demais, que correspondem "
            "a um padrão, ou todos os selecionados, como cabeçalhos de página."
        ),
        de=(
            "Entfernt Dokumentelemente, die zu kurz oder zu lang sind, einem "
            "Muster entsprechen, oder alle ausgewählten, etwa Kopfzeilen."
        ),
        zh="删除过短或过长、匹配某个模式的文档元素，或删除所有所选元素，例如页眉。",
    )
    metadata = {"allowed_types": [Text, DashAIImage], "allowed_dtypes": []}

    def __init__(
        self,
        rule: str = BY_LENGTH,
        min_characters: int = 1,
        max_characters: Optional[int] = None,
        pattern: Optional[str] = None,
    ) -> None:
        """Store the rule.

        Parameters
        ----------
        rule : str, optional
            One of ``RULES``. Default drops items by length.
        min_characters : int, optional
            Shortest kept length, without surrounding spaces. Default 1.
        max_characters : int, optional
            Longest kept length; no limit when None.
        pattern : str, optional
            Regular expression for the pattern rules.

        Raises
        ------
        ValueError
            If the rule is unknown, the length bounds are inverted, or a
            pattern rule has no valid pattern.
        """
        super().__init__()
        if rule not in RULES:
            raise ValueError(f"Unknown rule {rule!r}; choose one of {RULES}.")
        if max_characters is not None and max_characters < min_characters:
            raise ValueError(
                f"The maximum of {max_characters} characters is below the "
                f"minimum of {min_characters}."
            )
        self.rule = rule
        self.min_characters = min_characters
        self.max_characters = max_characters
        self.regex = None
        if rule in (MATCHING, NOT_MATCHING):
            if not pattern:
                raise ValueError(f"Write a pattern to use the rule {rule!r}.")
            try:
                self.regex = re.compile(pattern)
            except re.error as e:
                raise ValueError(f"The pattern {pattern!r} is not valid: {e}.") from e

    def _keeps(self, value: str) -> bool:
        """Tell whether a Text item survives the rule."""
        if self.rule == EVERY_ITEM:
            return False
        if self.rule == BY_LENGTH:
            length = len(value.strip())
            return length >= self.min_characters and (
                self.max_characters is None or length <= self.max_characters
            )
        found = self.regex.search(value) is not None
        return not found if self.rule == MATCHING else found

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Return the items the rule keeps, each from its own source.

        Parameters
        ----------
        x : DashAIDataset
            The selected items, in one column.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            The kept items with their source rows.

        Raises
        ------
        ValueError
            If a rule other than 'Every selected item' runs on Image items.
        """
        column = x.column_names[0]
        is_image = isinstance(x.types.get(column), DashAIImage)
        if is_image and self.rule != EVERY_ITEM:
            raise ValueError(
                f"The rule {self.rule!r} reads text; use 'Every selected item' "
                "to drop Image items."
            )
        values = x.arrow_table.column(column).to_pylist()
        kept = [] if is_image else [i for i, v in enumerate(values) if self._keeps(v)]
        return self.items_result(
            [values[index] for index in kept],
            kept,
            content_type=DashAIImage if is_image else Text,
        )
