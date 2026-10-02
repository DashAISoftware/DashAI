"""Document dataloader for PDF files using pdfplumber."""

from typing import TYPE_CHECKING, Any, ClassVar, Dict, List

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    float_field,
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


class PdfPlumberDocumentSchema(BaseSchema):
    """Parameters for PdfPlumberDocumentDataLoader."""

    password: schema_field(
        string_field(),
        placeholder="",
        description="Password for encrypted PDFs. Leave empty for unencrypted files.",
    )
    x_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Horizontal distance, in points, below which two characters belong to "
            "the same word. Lower it when words run together."
        ),
    )
    y_tolerance: schema_field(
        float_field(gt=0.0),
        placeholder=3.0,
        description=(
            "Vertical distance, in points, below which two characters belong to "
            "the same line. Raise it when a line is split in two."
        ),
    )
    layout: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Pad the output with whitespace so it mirrors the position of the text "
            "on the page. Preserves columns at the cost of extra whitespace."
        ),
    )
    extract_tables: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Store each detected table as its own text item of tab separated "
            "rows, right after the text of its page."
        ),
    )


class PdfPlumberDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pdfplumber: per page, its text, then its tables."""

    SCHEMA: ClassVar[BaseSchema] = PdfPlumberDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
    DEFAULT_PARAMS: ClassVar[Dict[str, Any]] = {
        "password": "",
        "x_tolerance": 3.0,
        "y_tolerance": 3.0,
        "layout": False,
        "extract_tables": False,
    }
    DISPLAY_NAME = MultilingualString(
        en="PDF (pdfplumber)",
        es="PDF (pdfplumber)",
        pt="PDF (pdfplumber)",
        de="PDF (pdfplumber)",
        zh="PDF (pdfplumber)",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads PDF files with pdfplumber, which detects words and tables. "
            "Stores the text of each page as one text item and, when enabled, "
            "each detected table as a separate text item of tab separated rows."
        ),
        es=(
            "Lee archivos PDF con pdfplumber, que detecta palabras y tablas. "
            "Guarda el texto de cada página como un elemento de texto y, si se "
            "activa, cada tabla detectada como otro elemento de texto con filas "
            "separadas por tabuladores."
        ),
        pt=(
            "Lê arquivos PDF com pdfplumber, que detecta palavras e tabelas. "
            "Guarda o texto de cada página como um item de texto e, quando "
            "ativado, cada tabela detectada como outro item de texto com linhas "
            "separadas por tabulações."
        ),
        de=(
            "Liest PDF-Dateien mit pdfplumber, das Wörter und Tabellen erkennt. "
            "Speichert den Text jeder Seite als ein Textelement und, falls "
            "aktiviert, jede erkannte Tabelle als eigenes Textelement mit "
            "tabulatorgetrennten Zeilen."
        ),
        zh=(
            "使用 pdfplumber 读取 PDF 文件，可识别单词和表格。将每一页的文本保存为"
            "一个文本项；启用后，每个识别出的表格会另存为以制表符分隔行的文本项。"
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

    def _read_pages(self, file_path: str, params: Dict[str, Any]) -> List[List[str]]:
        """Read the text parts of every page.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            Resolved parameters.

        Returns
        -------
        List[List[str]]
            Per page: the stripped text if not blank, then each non blank table.
        """
        import pdfplumber

        pages = []
        with pdfplumber.open(file_path, password=params["password"] or "") as pdf:
            for page in pdf.pages:
                parts = []
                text = page.extract_text(
                    x_tolerance=params["x_tolerance"],
                    y_tolerance=params["y_tolerance"],
                    layout=params["layout"],
                )
                if text and text.strip():
                    parts.append(text.strip())
                if params["extract_tables"]:
                    for table in page.extract_tables():
                        rendered = self.render_table(table)
                        if rendered.strip():
                            parts.append(rendered)
                pages.append(parts)
        return pages

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pdfplumber.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            pdfplumber parameters; missing keys take the defaults.

        Returns
        -------
        DashAIDocument
            Text items for page texts and tables, in reading order.

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
        items = [
            DocumentItem(type=Text, content=part, page=number)
            for number, parts in enumerate(pages, start=1)
            for part in parts
        ]
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, len(pages))
        )
