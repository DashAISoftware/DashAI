"""Document dataloader for PDF files using pypdf."""

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Dict, List, Tuple

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.document_blocks import (
    BLOCK_GRANULARITY,
    GRANULARITIES,
    split_blank_line_blocks,
)
from DashAI.back.dataloaders.classes.document_dataloader import (
    DocumentDataLoader,
    DocumentLoaderError,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument

log = logging.getLogger(__name__)


class PypdfDocumentSchema(BaseSchema):
    """Parameters for PypdfDocumentDataLoader."""

    strict: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Fail on a malformed PDF instead of trying to recover from it.",
            es=("Falla ante un PDF mal formado en lugar de intentar recuperarlo."),
            pt=("Falha diante de um PDF mal formado em vez de tentar recuperá-lo."),
            de=(
                "Bei einer fehlerhaften PDF abbrechen, statt zu versuchen sie "
                "zu retten."
            ),
            zh="遇到格式损坏的 PDF 时报错，而不是尝试修复。",
        ),
        alias=MultilingualString(
            en="Strict mode",
            es="Modo estricto",
            pt="Modo estrito",
            de="Strikter Modus",
            zh="严格模式",
        ),
    )  # type: ignore

    granularity: schema_field(
        enum_field(GRANULARITIES),
        placeholder=BLOCK_GRANULARITY,
        description=MultilingualString(
            en=(
                "How much text one item holds. One item per block splits a "
                "page wherever a blank line separates its text; one item per "
                "page keeps the whole page together. pypdf has no layout "
                "analysis, so a page whose text has no blank line stays a "
                "single item either way, while pdfminer.six finds real layout "
                "blocks."
            ),
            es=(
                "Cuánto texto guarda un elemento. Un elemento por bloque "
                "divide la página donde una línea en blanco separa su texto; "
                "un elemento por página mantiene la página completa. pypdf no "
                "analiza el diseño, así que una página sin líneas en blanco "
                "queda como un único elemento en ambos casos, mientras que "
                "pdfminer.six encuentra bloques de diseño reales."
            ),
            pt=(
                "Quanto texto um item guarda. Um item por bloco divide a "
                "página onde uma linha em branco separa o texto; um item por "
                "página mantém a página inteira. O pypdf não analisa o "
                "layout, então uma página sem linhas em branco fica como um "
                "único item nos dois casos, enquanto o pdfminer.six encontra "
                "blocos de layout reais."
            ),
            de=(
                "Wie viel Text ein Element enthält. Ein Element pro Block "
                "teilt eine Seite dort, wo eine Leerzeile ihren Text trennt; "
                "ein Element pro Seite behält die ganze Seite zusammen. pypdf "
                "analysiert kein Layout, daher bleibt eine Seite ohne "
                "Leerzeile in beiden Fällen ein einziges Element, während "
                "pdfminer.six echte Layoutblöcke findet."
            ),
            zh=(
                "一个项包含多少文本。每个文本块一个项会在空行处拆分页面；"
                "每页一个项则保留整页。pypdf 不做版面分析，"
                "因此没有空行的页面在两种设置下都只有一个项；"
                "pdfminer.six 能识别真正的版面块。"
            ),
        ),
        alias=MultilingualString(
            en="Granularity",
            es="Granularidad",
            pt="Granularidade",
            de="Granularität",
            zh="粒度",
        ),
    )  # type: ignore

    extract_images: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=(
                "Also store the images embedded in each page. They are placed "
                "after the text of their page in reading order."
            ),
            es=(
                "Guarda también las imágenes incrustadas en cada página. Se "
                "colocan después del texto de su página en el orden de "
                "lectura."
            ),
            pt=(
                "Guarda também as imagens incorporadas em cada página. Elas "
                "ficam depois do texto da sua página na ordem de leitura."
            ),
            de=(
                "Speichert auch die in jede Seite eingebetteten Bilder. Sie "
                "stehen in der Lesereihenfolge nach dem Text ihrer Seite."
            ),
            zh="同时保存每页中嵌入的图像。按阅读顺序排在该页文本之后。",
        ),
        alias=MultilingualString(
            en="Extract images",
            es="Extraer imágenes",
            pt="Extrair imagens",
            de="Bilder extrahieren",
            zh="提取图像",
        ),
    )  # type: ignore


class PypdfDocumentDataLoader(DocumentDataLoader):
    """Parse a PDF with pypdf: per page, its text blocks, then its images."""

    SCHEMA: ClassVar[BaseSchema] = PypdfDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset({".pdf"})
    DISPLAY_NAME = MultilingualString(
        en="pypdf",
        es="pypdf",
        pt="pypdf",
        de="pypdf",
        zh="pypdf",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads PDF files with pypdf. Stores the text of each page as one "
            "text item per blank line separated block, or as a single item per "
            "page, always with its page number, and can also store the images "
            "embedded in each page."
        ),
        es=(
            "Lee archivos PDF con pypdf. Guarda el texto de cada página como un "
            "elemento de texto por cada bloque separado por líneas en blanco, o "
            "como un único elemento por página, siempre con su número de página, "
            "y también puede guardar las imágenes incrustadas en cada página."
        ),
        pt=(
            "Lê arquivos PDF com pypdf. Guarda o texto de cada página como um "
            "item de texto por bloco separado por linhas em branco, ou como um "
            "único item por página, sempre com o número da página, e também pode "
            "guardar as imagens incorporadas em cada página."
        ),
        de=(
            "Liest PDF-Dateien mit pypdf. Speichert den Text jeder Seite als ein "
            "Textelement pro durch Leerzeilen getrenntem Block oder als ein "
            "einziges Element pro Seite, immer mit Seitennummer, und kann auch "
            "die in jede Seite eingebetteten Bilder speichern."
        ),
        zh=(
            "使用 pypdf 读取 PDF 文件。将每一页的文本按空行分隔的块分别保存为"
            "文本项，或整页保存为一个文本项，均带页码；并可选择保存每页中嵌入的图像。"
        ),
    )

    @staticmethod
    def _page_images(page: Any) -> List[Tuple[str, bytes]]:
        """Decode the embedded images of one page, skipping broken ones.

        Parameters
        ----------
        page : pypdf.PageObject
            The page to read.

        Returns
        -------
        List[Tuple[str, bytes]]
            ``(name, data)`` of each decodable image, in pypdf's order.
        """
        try:
            total = len(page.images)
        except Exception as e:
            log.warning("pypdf could not list the images of a page: %s", e)
            return []
        images = []
        for index in range(total):
            try:
                image = page.images[index]
                images.append((image.name, image.data))
            except Exception as e:
                log.warning("pypdf could not decode image %d: %s", index, e)
        return images

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Parse a PDF with pypdf.

        Parameters
        ----------
        file_path : str
            Path of the PDF file.
        params : Dict[str, Any]
            ``strict``, ``granularity`` and ``extract_images``; missing keys
            take the defaults.

        Returns
        -------
        DashAIDocument
            Text and Image items in reading order.

        Raises
        ------
        DocumentLoaderError
            If pypdf cannot read the file.
        """
        from pypdf import PdfReader

        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.dashai_image import DashAIImage
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        blocks = resolved["granularity"] == BLOCK_GRANULARITY
        items = []
        try:
            reader = PdfReader(file_path, strict=resolved["strict"])
            for number, page in enumerate(reader.pages, start=1):
                text = (page.extract_text() or "").strip()
                parts = split_blank_line_blocks(text) if blocks else [text]
                items.extend(
                    DocumentItem(type=Text, content=part, page=number)
                    for part in parts
                    if part
                )
                if resolved["extract_images"]:
                    for name, data in self._page_images(page):
                        items.append(
                            DocumentItem(
                                type=DashAIImage,
                                content=self.web_image(data, name),
                                page=number,
                            )
                        )
            n_pages = len(reader.pages)
        except Exception as e:
            raise DocumentLoaderError(f"pypdf failed to read {file_path}: {e}") from e
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, n_pages)
        )
