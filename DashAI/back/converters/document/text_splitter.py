"""Split Text items into sentences, lines or paragraphs."""

import re
from typing import TYPE_CHECKING, List, Union

from DashAI.back.converters.category.document_processing import (
    DocumentProcessingConverter,
)
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.core.schema_fields import enum_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

SENTENCES = "Sentences"
LINES = "Lines"
PARAGRAPHS = "Paragraphs"
BOUNDARIES = {
    SENTENCES: re.compile(
        r"(?<=[.!?…])\s+|(?<=[.!?…][\"'”’)\]])\s+|\r?\n[^\S\r\n]*\r?\n\s*"
    ),
    LINES: re.compile(r"\r?\n"),
    PARAGRAPHS: re.compile(r"\r?\n[^\S\r\n]*\r?\n\s*"),
}


class TextSplitterSchema(BaseSchema):
    """Schema for the text splitter."""

    split_by: schema_field(
        enum_field(list(BOUNDARIES)),
        SENTENCES,
        description=MultilingualString(
            en=(
                "Where to cut each item. Sentences end at '.', '!', '?' or a "
                "blank line; paragraphs are separated by blank lines."
            ),
            es=(
                "Dónde cortar cada elemento. Las oraciones terminan en '.', '!', "
                "'?' o una línea en blanco; los párrafos se separan por líneas "
                "en blanco."
            ),
            pt=(
                "Onde cortar cada item. Frases terminam em '.', '!', '?' ou uma "
                "linha em branco; parágrafos são separados por linhas em branco."
            ),
            de=(
                "Wo jedes Element geteilt wird. Sätze enden mit '.', '!', '?' "
                "oder einer Leerzeile; Absätze sind durch Leerzeilen getrennt."
            ),
            zh="每个元素的切分位置。句子以 '.'、'!'、'?' 或空行结束；段落以空行分隔。",
        ),
        alias=MultilingualString(
            en="Split by",
            es="Dividir por",
            pt="Dividir por",
            de="Teilen nach",
            zh="切分方式",
        ),
    )  # type: ignore


class TextSplitter(DocumentProcessingConverter, DocumentConverter):
    """Split each selected Text item into several items.

    Each piece becomes its own item, right after the previous piece and on
    the same page, with the kind and attributes of the item it came from.
    Pieces of a table become paragraphs. Empty pieces are dropped.
    """

    SCHEMA = TextSplitterSchema
    DISPLAY_NAME = MultilingualString(
        en="Text Splitter",
        es="Divisor de Texto",
        pt="Divisor de Texto",
        de="Textteiler",
        zh="文本切分器",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Splits Text items into sentences, lines or paragraphs, each one a "
            "new item on the same page."
        ),
        es=(
            "Divide los elementos de texto en oraciones, líneas o párrafos, cada "
            "uno como un nuevo elemento en la misma página."
        ),
        pt=(
            "Divide itens de texto em frases, linhas ou parágrafos, cada um como "
            "um novo item na mesma página."
        ),
        de=(
            "Teilt Textelemente in Sätze, Zeilen oder Absätze, jeweils als neues "
            "Element auf derselben Seite."
        ),
        zh="将文本元素切分为句子、行或段落，每一部分成为同一页上的新元素。",
    )
    metadata = {"allowed_types": [Text], "allowed_dtypes": []}

    def __init__(self, split_by: str = SENTENCES) -> None:
        """Store where items are cut.

        Parameters
        ----------
        split_by : str, optional
            ``"Sentences"`` (default), ``"Lines"`` or ``"Paragraphs"``.

        Raises
        ------
        ValueError
            If ``split_by`` is not one of those.
        """
        super().__init__()
        if split_by not in BOUNDARIES:
            raise ValueError(
                f"Unknown split {split_by!r}; choose one of {list(BOUNDARIES)}."
            )
        self.split_by = split_by

    def split(self, value: str) -> List[str]:
        """Cut one text into its non empty pieces.

        Parameters
        ----------
        value : str
            The text to cut.

        Returns
        -------
        List[str]
            The pieces without surrounding whitespace, in order.
        """
        pieces = (piece.strip() for piece in BOUNDARIES[self.split_by].split(value))
        return [piece for piece in pieces if piece]

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Return the pieces of every selected item.

        Parameters
        ----------
        x : DashAIDataset
            The selected Text items, in one column.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            One row per piece, with the index of the item it came from.
        """
        contents: List[str] = []
        sources: List[int] = []
        for index, value in enumerate(x.arrow_table.column(0).to_pylist()):
            for piece in self.split(value):
                contents.append(piece)
                sources.append(index)
        return self.items_result(contents, sources)
