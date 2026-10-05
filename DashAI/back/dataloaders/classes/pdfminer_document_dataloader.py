"""Document dataloader for PDF files using pdfminer.six."""

from typing import TYPE_CHECKING, Any, ClassVar, Dict

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
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


class PdfMinerDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pdfminer.six into one Text item per page.

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
            "which helps with documents that have several columns. Stores the "
            "text of each page as one text item with its page number."
        ),
        es=(
            "Lee archivos PDF con pdfminer.six y su análisis de diseño ajustable, "
            "útil en documentos con varias columnas. Guarda el texto de cada "
            "página como un elemento de texto con su número de página."
        ),
        pt=(
            "Lê arquivos PDF com pdfminer.six e sua análise de layout ajustável, "
            "útil em documentos com várias colunas. Guarda o texto de cada página "
            "como um item de texto com o número da página."
        ),
        de=(
            "Liest PDF-Dateien mit pdfminer.six und seiner einstellbaren "
            "Layoutanalyse, hilfreich bei mehrspaltigen Dokumenten. Speichert den "
            "Text jeder Seite als ein Textelement mit Seitennummer."
        ),
        zh=(
            "使用 pdfminer.six 及其可调的版面分析读取 PDF 文件，适用于多栏文档。"
            "将每一页的文本保存为带页码的文本项。"
        ),
    )

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pdfminer.six.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            Layout parameters; missing keys take the defaults.

        Returns
        -------
        DashAIDocument
            One Text item per page with text, in page order.

        Raises
        ------
        DocumentLoaderError
            If pdfminer.six cannot read the file.
        """
        from pdfminer.high_level import extract_text
        from pdfminer.layout import LAParams

        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        try:
            text = extract_text(
                file_path,
                password=resolved["password"] or "",
                laparams=LAParams(
                    line_margin=resolved["line_margin"],
                    char_margin=resolved["char_margin"],
                    boxes_flow=resolved["boxes_flow"],
                    detect_vertical=resolved["detect_vertical"],
                ),
            )
        except Exception as e:
            raise DocumentLoaderError(
                f"pdfminer.six failed to read {file_path}: {e}"
            ) from e
        pages = text.split("\f")
        if pages and pages[-1] == "":
            pages.pop()
        items = [
            DocumentItem(type=Text, content=page.strip(), page=number)
            for number, page in enumerate(pages, start=1)
            if page.strip()
        ]
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, len(pages))
        )
