from typing import Final

from DashAI.back.converters.base_converter import BaseConverter
from DashAI.back.core.data_kinds import DOCUMENT
from DashAI.back.core.utils import MultilingualString
from DashAI.back.static.icons import Icon


class DocumentProcessingConverter(BaseConverter):
    """Base class for converters that prepare the items of a document.

    Document processing converters clean, rewrite, split, filter or read the
    Text and Image items of a document, for example after extracting a PDF
    or before indexing it for RAG.
    """

    CATEGORY = MultilingualString(
        en="Document Processing",
        es="Procesamiento de Documentos",
        pt="Processamento de Documentos",
        de="Dokumentverarbeitung",
        zh="文档处理",
    )
    ICON: Final[str] = Icon.Description.value
    COLOR: Final[str] = "rgb(52, 152, 219)"
    LEARNS_FROM_DATA = False
    metadata = {"data_kinds": [DOCUMENT]}
