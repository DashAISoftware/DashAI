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
        description=(
            "If True, raises errors on malformed PDFs. If False, tries to recover."
        ),
    )  # type: ignore

    granularity: schema_field(
        enum_field(GRANULARITIES),
        placeholder=BLOCK_GRANULARITY,
        description=(
            "How much text one item holds. 'block' splits a page wherever a "
            "blank line separates its text, 'page' keeps the whole page as one "
            "item. pypdf has no layout analysis, so a page whose text has no "
            "blank line stays a single item either way; pdfminer.six finds real "
            "layout blocks."
        ),
    )  # type: ignore

    extract_images: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Also store the images embedded in each page. They are placed after "
            "the text of their page in reading order."
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
                                content=DashAIImage(bytes=data, path=name),
                                page=number,
                            )
                        )
            n_pages = len(reader.pages)
        except Exception as e:
            raise DocumentLoaderError(f"pypdf failed to read {file_path}: {e}") from e
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, n_pages)
        )
