"""Document dataloader for PDF files using pdfminer.six."""

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


class PdfMinerDocumentSchema(BaseSchema):
    """Parameters for PdfMinerDocumentDataLoader."""

    password: schema_field(
        none_type(string_field()),
        placeholder=None,
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )  # type: ignore
    line_margin: schema_field(
        float_field(ge=0.0),
        placeholder=0.5,
        description=(
            "Vertical gap, as a fraction of line height, below which two lines "
            "belong to the same paragraph. Raise it to merge tight line spacing."
        ),
    )  # type: ignore
    char_margin: schema_field(
        float_field(ge=0.0),
        placeholder=2.0,
        description=(
            "Horizontal gap, as a fraction of character width, below which two "
            "characters belong to the same word. Lower it to split joined text."
        ),
    )  # type: ignore
    boxes_flow: schema_field(
        float_field(ge=-1.0, le=1.0),
        placeholder=0.5,
        description=(
            "How much reading order follows horizontal position over vertical "
            "position. -1.0 is strictly left to right, 1.0 strictly top to bottom."
        ),
    )  # type: ignore
    detect_vertical: schema_field(
        bool_field(),
        placeholder=False,
        description="Detect vertically written text, as used in CJK layouts.",
    )  # type: ignore
    granularity: schema_field(
        enum_field(GRANULARITIES),
        placeholder=BLOCK_GRANULARITY,
        description=(
            "How much text one item holds. 'block' stores each layout block "
            "pdfminer finds, such as a paragraph or a heading, as its own item. "
            "'page' keeps the whole page as one item. Blocks never cross a page "
            "boundary."
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


class PdfMinerDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pdfminer.six into Text items.

    With 'block' granularity every layout block pdfminer finds becomes its
    own item, and a block set in a larger font than the body text is named a
    heading. With 'page' granularity the text of a page becomes one item:
    pdfminer's text converter writes a form feed after every page, so the
    document text split on it gives the pages in order.
    """

    SCHEMA: ClassVar[BaseSchema] = PdfMinerDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
    DISPLAY_NAME = MultilingualString(
        en="pdfminer.six",
        es="pdfminer.six",
        pt="pdfminer.six",
        de="pdfminer.six",
        zh="pdfminer.six",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads PDF files with pdfminer.six and its tunable layout analysis, "
            "which helps with documents that have several columns. Stores each "
            "layout block it finds, such as a paragraph or a heading, as one "
            "text item with its page number, or the whole text of a page as a "
            "single item."
        ),
        es=(
            "Lee archivos PDF con pdfminer.six y su análisis de diseño ajustable, "
            "útil en documentos con varias columnas. Guarda cada bloque de "
            "diseño que encuentra, como un párrafo o un título, como un "
            "elemento de texto con su número de página, o todo el texto de la "
            "página como un único elemento."
        ),
        pt=(
            "Lê arquivos PDF com pdfminer.six e sua análise de layout ajustável, "
            "útil em documentos com várias colunas. Guarda cada bloco de layout "
            "que encontra, como um parágrafo ou um título, como um item de texto "
            "com o número da página, ou todo o texto da página como um único "
            "item."
        ),
        de=(
            "Liest PDF-Dateien mit pdfminer.six und seiner einstellbaren "
            "Layoutanalyse, hilfreich bei mehrspaltigen Dokumenten. Speichert "
            "jeden gefundenen Layoutblock, etwa einen Absatz oder eine "
            "Überschrift, als ein Textelement mit Seitennummer, oder den ganzen "
            "Text einer Seite als ein einziges Element."
        ),
        zh=(
            "使用 pdfminer.six 及其可调的版面分析读取 PDF 文件，适用于多栏文档。"
            "将识别出的每个版面块（如段落或标题）保存为带页码的文本项，"
            "或将整页文本保存为一个文本项。"
        ),
    )

    @staticmethod
    def _layout_params(resolved: Dict[str, Any]) -> Any:
        """Build the pdfminer layout parameters from the resolved schema.

        Parameters
        ----------
        resolved : Dict[str, Any]
            The resolved loader parameters.

        Returns
        -------
        pdfminer.layout.LAParams
            The layout parameters both granularities share.
        """
        from pdfminer.layout import LAParams

        return LAParams(
            line_margin=resolved["line_margin"],
            char_margin=resolved["char_margin"],
            boxes_flow=resolved["boxes_flow"],
            detect_vertical=resolved["detect_vertical"],
        )

    @staticmethod
    def _char_sizes(element: Any) -> List[float]:
        """Collect the font size of every character of a layout element.

        Parameters
        ----------
        element : pdfminer.layout.LTComponent
            A layout element, usually a text container.

        Returns
        -------
        List[float]
            The size of each character found below ``element``.
        """
        from pdfminer.layout import LTChar

        sizes = []
        pending = [element]
        while pending:
            node = pending.pop()
            if isinstance(node, LTChar):
                sizes.append(node.size)
            elif hasattr(node, "__iter__"):
                pending.extend(node)
        return sizes

    def _read_blocks(
        self, file_path: str, resolved: Dict[str, Any]
    ) -> List[List[Tuple[str, Optional[float]]]]:
        """Read every page as its layout blocks with their font size.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        resolved : Dict[str, Any]
            The resolved loader parameters.

        Returns
        -------
        List[List[Tuple[str, Optional[float]]]]
            Per page, each non blank block as its text and its font size, in
            the reading order pdfminer's layout analysis gives.
        """
        from pdfminer.high_level import extract_pages
        from pdfminer.layout import LTTextContainer

        pages = []
        for layout in extract_pages(
            file_path,
            password=resolved["password"] or "",
            laparams=self._layout_params(resolved),
        ):
            blocks = []
            for element in layout:
                if not isinstance(element, LTTextContainer):
                    continue
                text = element.get_text().strip()
                if text:
                    size = representative_size(self._char_sizes(element))
                    blocks.append((text, size))
            pages.append(blocks)
        return pages

    def _read_page_texts(
        self, file_path: str, resolved: Dict[str, Any]
    ) -> List[List[Tuple[str, Optional[float]]]]:
        """Read every page as a single block holding its whole text.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        resolved : Dict[str, Any]
            The resolved loader parameters.

        Returns
        -------
        List[List[Tuple[str, Optional[float]]]]
            Per page, its stripped text as one block without a font size, or
            no block when the page has no text.
        """
        from pdfminer.high_level import extract_text

        text = extract_text(
            file_path,
            password=resolved["password"] or "",
            laparams=self._layout_params(resolved),
        )
        pages = text.split("\f")
        if pages and pages[-1] == "":
            pages.pop()
        return [[(page.strip(), None)] if page.strip() else [] for page in pages]

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pdfminer.six.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            Layout parameters, ``granularity`` and ``detect_headings``;
            missing keys take the defaults.

        Returns
        -------
        DashAIDocument
            One Text item per layout block, or one per page with text, in
            reading order. Short blocks set larger than the body text are
            named headings when ``detect_headings`` is on.

        Raises
        ------
        DocumentLoaderError
            If pdfminer.six cannot read the file.
        """
        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        as_blocks = resolved["granularity"] == BLOCK_GRANULARITY
        try:
            pages = (
                self._read_blocks(file_path, resolved)
                if as_blocks
                else self._read_page_texts(file_path, resolved)
            )
        except Exception as e:
            raise DocumentLoaderError(
                f"pdfminer.six failed to read {file_path}: {e}"
            ) from e
        blocks = [block for page in pages for block in page]
        numbers = [number for number, page in enumerate(pages, start=1) for _ in page]
        elements = (
            name_blocks(blocks)
            if as_blocks and resolved["detect_headings"]
            else [("paragraph", {})] * len(blocks)
        )
        items = [
            DocumentItem(type=Text, content=text, page=number, kind=kind, attrs=attrs)
            for (text, _), number, (kind, attrs) in zip(
                blocks, numbers, elements, strict=True
            )
        ]
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, len(pages))
        )
