"""Document dataloader for plain text files."""

import re
from typing import TYPE_CHECKING, Any, ClassVar, Dict

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dataloaders.classes.document_dataloader import (
    DocumentDataLoader,
    DocumentLoaderError,
)

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_document import DashAIDocument

_PARAGRAPH_BREAK = re.compile(r"\n\s*\n")


class PlainTextDocumentSchema(BaseSchema):
    """Parameters for PlainTextDocumentDataLoader."""

    encoding: schema_field(
        enum_field(["utf-8", "latin1", "cp1252", "iso-8859-1"]),
        placeholder="utf-8",
        description="File encoding",
    )  # type: ignore

    split_paragraphs: schema_field(
        bool_field(),
        placeholder=False,
        description=(
            "Store each paragraph, separated by blank lines, as its own text "
            "item. Turn it off to keep the whole file as a single text item."
        ),
    )  # type: ignore


class PlainTextDocumentDataLoader(DocumentDataLoader):
    """Parse a text file into paragraphs, or into one Text item for the file."""

    SCHEMA: ClassVar[BaseSchema] = PlainTextDocumentSchema
    SUPPORTED_EXTENSIONS: frozenset[str] = frozenset(
        {".txt", ".md", ".rst", ".tex", ".csv"}
    )
    DISPLAY_NAME = MultilingualString(
        en="Plain text",
        es="Texto plano",
        pt="Texto simples",
        de="Klartext",
        zh="纯文本",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Reads plain text files (txt, md, rst, tex, csv) with a configurable "
            "encoding. Stores each paragraph, separated by blank lines, as one "
            "text item, or the whole file as a single text item."
        ),
        es=(
            "Lee archivos de texto plano (txt, md, rst, tex, csv) con una "
            "codificación configurable. Guarda cada párrafo, separado por líneas "
            "en blanco, como un elemento de texto, o el archivo completo como un "
            "único elemento de texto."
        ),
        pt=(
            "Lê arquivos de texto simples (txt, md, rst, tex, csv) com uma "
            "codificação configurável. Guarda cada parágrafo, separado por linhas "
            "em branco, como um item de texto, ou o arquivo inteiro como um único "
            "item de texto."
        ),
        de=(
            "Liest Klartextdateien (txt, md, rst, tex, csv) mit einstellbarer "
            "Kodierung. Speichert jeden durch Leerzeilen getrennten Absatz als ein "
            "Textelement oder die ganze Datei als ein einziges Textelement."
        ),
        zh=(
            "以可配置的编码读取纯文本文件（txt、md、rst、tex、csv）。"
            "将以空行分隔的每个段落保存为一个文本项，或将整个文件保存为一个文本项。"
        ),
    )

    def load_document(self, file_path: str, params: Dict[str, Any]) -> "DashAIDocument":
        """Read a text file into paragraphs or into one text item.

        Parameters
        ----------
        file_path : str
            Path of the text file.
        params : Dict[str, Any]
            ``encoding`` and ``split_paragraphs``; missing keys take their
            defaults.

        Returns
        -------
        DashAIDocument
            One Text item per blank line separated paragraph when
            ``split_paragraphs`` is True, else one Text item with the whole
            stripped text; no item for a blank file; ``page=None``.

        Raises
        ------
        DocumentLoaderError
            If the file cannot be read or decoded.
        """
        from DashAI.back.dataloaders.classes.dashai_document import (
            DashAIDocument,
            DocumentItem,
        )
        from DashAI.back.types.value_types import Text

        resolved = self.resolve_params(params)
        encoding = resolved["encoding"] or "utf-8"
        try:
            with open(file_path, "r", encoding=encoding) as handle:
                text = handle.read()
        except (OSError, UnicodeDecodeError, LookupError) as e:
            raise DocumentLoaderError(
                f"Error reading {file_path} with encoding '{encoding}': {e}"
            ) from e
        parts = _PARAGRAPH_BREAK.split(text) if resolved["split_paragraphs"] else [text]
        items = [
            DocumentItem(type=Text, content=part.strip())
            for part in parts
            if part.strip()
        ]
        return DashAIDocument.from_items(
            items, metadata=self.build_metadata(file_path, resolved, None)
        )
