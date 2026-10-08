"""Document dataloader for PDF files using pdfplumber."""

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Optional, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.document_blocks import (
    BLOCK_GRANULARITY,
    GRANULARITIES,
    name_blocks,
    representative_size,
)
from DashAI.back.dataloaders.classes.document_dataloader import (
    DocumentDataLoader,
    DocumentLoaderError,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument


class PdfPlumberDocumentSchema(BaseSchema):
    """Parameters for PdfPlumberDocumentDataLoader."""

    password: schema_field(
        none_type(string_field()),
        placeholder=None,
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )  # type: ignore
    x_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Horizontal distance, in points, below which two characters belong to "
            "the same word. Lower it when words run together."
        ),
    )  # type: ignore
    y_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Vertical distance, in points, below which two characters belong to "
            "the same line. Raise it when a line is split in two."
        ),
    )  # type: ignore
    layout: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Pad the output with whitespace so it mirrors the position of the text "
            "on the page. Preserves columns at the cost of extra whitespace."
        ),
    )  # type: ignore
    extract_tables: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Store each detected table as its own text item of tab separated "
            "rows, right after the text of its page."
        ),
    )  # type: ignore
    granularity: schema_field(
        enum_field(GRANULARITIES),
        placeholder=BLOCK_GRANULARITY,
        description=(
            "How much text one item holds. 'block' groups the lines of a page "
            "into blocks and stores each one as its own item, 'page' keeps the "
            "whole page as one item. Blocks never cross a page boundary."
        ),
    )  # type: ignore
    block_gap: schema_field(
        float_field(gt=0.0),
        placeholder=0.6,
        description=(
            "Vertical gap between two lines, as a fraction of line height, "
            "above which a new block starts. Raise it to join lines that sit "
            "far apart. Only used with 'block' granularity."
        ),
    )  # type: ignore
    detect_headings: schema_field(
        bool_field(),
        placeholder=True,
        description=(
            "Name short blocks set in a font larger than the body text as "
            "headings, with a level from the rank of their size. Only used with "
            "'block' granularity."
        ),
    )  # type: ignore


class PdfPlumberDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pdfplumber: per page, its text blocks, then its tables.

    With 'block' granularity the lines of a page are grouped into blocks by
    the gap between them and by their font size, and a short block set larger
    than the body text is named a heading. With 'page' granularity the text
    of a page becomes one item.
    """

    SCHEMA: ClassVar[BaseSchema] = PdfPlumberDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
    DISPLAY_NAME = MultilingualString(
        en="pdfplumber",
        es="pdfplumber",
        pt="pdfplumber",
        de="pdfplumber",
        zh="pdfplumber",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads PDF files with pdfplumber, which detects words and tables. "
            "Groups the lines of a page into blocks and stores each one as a "
            "text item, or keeps the whole page as a single item, and when "
            "enabled stores each detected table as a separate text item of tab "
            "separated rows."
        ),
        es=(
            "Lee archivos PDF con pdfplumber, que detecta palabras y tablas. "
            "Agrupa las líneas de una página en bloques y guarda cada uno como "
            "un elemento de texto, o conserva la página completa como un único "
            "elemento, y si se activa guarda cada tabla detectada como otro "
            "elemento de texto con filas separadas por tabuladores."
        ),
        pt=(
            "Lê arquivos PDF com pdfplumber, que detecta palavras e tabelas. "
            "Agrupa as linhas de uma página em blocos e guarda cada um como um "
            "item de texto, ou mantém a página inteira como um único item, e "
            "quando ativado guarda cada tabela detectada como outro item de "
            "texto com linhas separadas por tabulações."
        ),
        de=(
            "Liest PDF-Dateien mit pdfplumber, das Wörter und Tabellen erkennt. "
            "Gruppiert die Zeilen einer Seite zu Blöcken und speichert jeden "
            "als Textelement, oder behält die ganze Seite als ein einziges "
            "Element, und speichert, falls aktiviert, jede erkannte Tabelle als "
            "eigenes Textelement mit tabulatorgetrennten Zeilen."
        ),
        zh=(
            "使用 pdfplumber 读取 PDF 文件，可识别单词和表格。将页面中的行分组为"
            "文本块并分别保存为文本项，或整页保存为一个文本项；启用后，"
            "每个识别出的表格会另存为以制表符分隔行的文本项。"
        ),
    )

    @staticmethod
    def render_table(table: List[List[object]]) -> str:
        """Render one table as tab separated rows.

        Parameters
        ----------
        table : List[List[object]]
            Rows of cells as pdfplumber returns them; empty cells are None.

        Returns
        -------
        str
            Newline separated rows of tab separated cells.
        """
        return "\n".join(
            "\t".join(str(cell) if cell else "" for cell in row) for row in table
        )

    @staticmethod
    def table_rows(table: List[List[object]]) -> List[List[str]]:
        """Turn one pdfplumber table into rows of string cells.

        Parameters
        ----------
        table : List[List[object]]
            Rows of cells as pdfplumber returns them; empty cells are None.

        Returns
        -------
        List[List[str]]
            The same rows with every cell as a string, empty cells as "".
        """
        return [[str(cell) if cell else "" for cell in row] for row in table]

    @staticmethod
    def _line_sizes(line: Dict[str, Any]) -> List[float]:
        """Return the font size of every character of one extracted line."""
        return [char["size"] for char in line.get("chars") or [] if char.get("size")]

    @classmethod
    def _starts_block(
        cls,
        previous: Dict[str, Any],
        line: Dict[str, Any],
        block_gap: float,
    ) -> bool:
        """Tell whether a line opens a new block instead of continuing one.

        A line starts a block when it sits further below the previous line
        than ``block_gap`` line heights, or when its font size differs, which
        is what separates a heading from the paragraph under it.

        Parameters
        ----------
        previous : Dict[str, Any]
            The line above, as ``extract_text_lines`` returns it.
        line : Dict[str, Any]
            The line being placed.
        block_gap : float
            Gap above which a new block starts, in line heights.

        Returns
        -------
        bool
            True when ``line`` opens a new block.
        """
        height = max(previous["bottom"] - previous["top"], 1e-6)
        if line["top"] - previous["bottom"] > block_gap * height:
            return True
        before = representative_size(cls._line_sizes(previous))
        current = representative_size(cls._line_sizes(line))
        return before is not None and current is not None and before != current

    @classmethod
    def _group_lines(
        cls, lines: List[Dict[str, Any]], block_gap: float
    ) -> List[Tuple[str, Optional[float]]]:
        """Group the lines of a page into blocks.

        Parameters
        ----------
        lines : List[Dict[str, Any]]
            The lines of one page, as ``extract_text_lines`` returns them.
        block_gap : float
            Gap above which a new block starts, in line heights.

        Returns
        -------
        List[Tuple[str, Optional[float]]]
            Each block as its newline joined text and its font size, in
            reading order.
        """
        blocks: List[Tuple[str, Optional[float]]] = []
        texts: List[str] = []
        sizes: List[float] = []
        previous = None
        for line in lines:
            text = (line.get("text") or "").strip()
            if not text:
                continue
            if previous is not None and cls._starts_block(previous, line, block_gap):
                blocks.append(("\n".join(texts), representative_size(sizes)))
                texts, sizes = [], []
            texts.append(text)
            sizes.extend(cls._line_sizes(line))
            previous = line
        if texts:
            blocks.append(("\n".join(texts), representative_size(sizes)))
        return blocks

    def _page_text_parts(
        self, page: Any, params: Dict[str, Any]
    ) -> List[Tuple[str, Optional[float]]]:
        """Return the text blocks of one page, honouring the granularity."""
        if params["granularity"] == BLOCK_GRANULARITY:
            lines = page.extract_text_lines(
                x_tolerance=params["x_tolerance"],
                y_tolerance=params["y_tolerance"],
                layout=params["layout"],
            )
            return self._group_lines(lines, params["block_gap"])
        text = page.extract_text(
            x_tolerance=params["x_tolerance"],
            y_tolerance=params["y_tolerance"],
            layout=params["layout"],
        )
        return [(text.strip(), None)] if text and text.strip() else []

    def _read_pages(self, file_path: str, params: Dict[str, Any]) -> List[List[Any]]:
        """Read the text parts of every page.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            Resolved parameters.

        Returns
        -------
        List[List[Any]]
            Per page: each text block as a ``(text, font size)`` tuple, then
            each non blank table as its raw rows (a list).
        """
        import pdfplumber

        pages = []
        with pdfplumber.open(file_path, password=params["password"] or "") as pdf:
            for page in pdf.pages:
                parts: List[Any] = list(self._page_text_parts(page, params))
                if params["extract_tables"]:
                    for table in page.extract_tables():
                        if self.render_table(table).strip():
                            parts.append(table)
                pages.append(parts)
        return pages

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pdfplumber.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            pdfplumber parameters, ``granularity``, ``block_gap`` and
            ``detect_headings``; missing keys take the defaults.

        Returns
        -------
        DashAIDocument
            Text items for the blocks of each page, named as headings when
            they stand out, and table items with their rows, in reading
            order.

        Raises
        ------
        DocumentLoaderError
            If pdfplumber cannot read the file.
        """
        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        try:
            pages = self._read_pages(file_path, resolved)
        except Exception as e:
            raise DocumentLoaderError(
                f"pdfplumber failed to read {file_path}: {e}"
            ) from e
        flat = [
            (number, part)
            for number, parts in enumerate(pages, start=1)
            for part in parts
        ]
        texts = [part for _, part in flat if isinstance(part, tuple)]
        named = (
            name_blocks(texts)
            if resolved["granularity"] == BLOCK_GRANULARITY
            and resolved["detect_headings"]
            else [("paragraph", {})] * len(texts)
        )
        elements = iter(named)
        items = []
        for number, part in flat:
            if isinstance(part, tuple):
                kind, attrs = next(elements)
                items.append(
                    DocumentItem(
                        type=Text,
                        content=part[0],
                        page=number,
                        kind=kind,
                        attrs=attrs,
                    )
                )
                continue
            items.append(
                DocumentItem(
                    type=Text,
                    content=self.render_table(part),
                    page=number,
                    kind="table",
                    attrs={"rows": self.table_rows(part)},
                )
            )
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, len(pages))
        )
