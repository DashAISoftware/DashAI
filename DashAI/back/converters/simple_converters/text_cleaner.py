"""Clean common extraction artifacts from text values."""

import re
import unicodedata

from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.converters.simple_converters.text_value_converter import (
    TextValueConverter,
)
from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.schema_fields import bool_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Text

HYPHEN_BREAK = re.compile(r"(?<=\w)-[ \t]*\r?\n[ \t]*(?=\w)")
INLINE_SPACE = re.compile(r"[^\S\r\n]+")
SPACE_AT_LINE_EDGE = re.compile(r"[^\S\r\n]*(\r?\n)[^\S\r\n]*")
BLANK_LINES = re.compile(r"(\r?\n){3,}")
KEPT_CONTROLS = {"\n", "\r", "\t"}


class TextCleanerSchema(BaseSchema):
    """Schema for the text cleaner."""

    normalize_unicode: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Apply Unicode NFKC normalization: ligatures such as 'ﬁ' become "
                "'fi' and full width or styled characters become plain ones."
            ),
            es=(
                "Aplica la normalización Unicode NFKC: ligaduras como 'ﬁ' pasan a "
                "'fi' y los caracteres de ancho completo o con estilo pasan a "
                "caracteres simples."
            ),
            pt=(
                "Aplica a normalização Unicode NFKC: ligaduras como 'ﬁ' viram "
                "'fi' e caracteres de largura total ou estilizados viram "
                "caracteres simples."
            ),
            de=(
                "Wendet die Unicode NFKC Normalisierung an: Ligaturen wie 'ﬁ' "
                "werden zu 'fi', Zeichen voller Breite oder mit Stil zu "
                "einfachen Zeichen."
            ),
            zh=(
                "应用 Unicode NFKC 规范化：'ﬁ' 等连字变为 'fi'，全角或样式字符变为普通"
                "字符。"
            ),
        ),
        alias=MultilingualString(
            en="Normalize Unicode",
            es="Normalizar Unicode",
            pt="Normalizar Unicode",
            de="Unicode normalisieren",
            zh="规范化 Unicode",
        ),
    )  # type: ignore
    join_hyphenated: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Rejoin words split by a hyphen at the end of a line, as in "
                "'exam-' and 'ple' on the next line."
            ),
            es=(
                "Une las palabras cortadas con guion al final de una línea, como "
                "'ejem-' y 'plo' en la línea siguiente."
            ),
            pt=(
                "Une palavras cortadas por hífen no fim de uma linha, como "
                "'exem-' e 'plo' na linha seguinte."
            ),
            de=(
                "Fügt am Zeilenende mit Bindestrich getrennte Wörter wieder "
                "zusammen, etwa 'Bei-' und 'spiel' in der nächsten Zeile."
            ),
            zh="重新连接在行尾被连字符拆开的单词。",
        ),
        alias=MultilingualString(
            en="Join hyphenated words",
            es="Unir palabras con guion",
            pt="Unir palavras com hífen",
            de="Getrennte Wörter verbinden",
            zh="连接连字符拆分的单词",
        ),
    )  # type: ignore
    remove_control_characters: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Remove invisible control and format characters, such as zero "
                "width spaces and soft hyphens. Line breaks and tabs are kept."
            ),
            es=(
                "Elimina caracteres invisibles de control y formato, como "
                "espacios de ancho cero y guiones suaves. Se conservan los "
                "saltos de línea y las tabulaciones."
            ),
            pt=(
                "Remove caracteres invisíveis de controle e formatação, como "
                "espaços de largura zero e hifens suaves. Quebras de linha e "
                "tabulações são mantidas."
            ),
            de=(
                "Entfernt unsichtbare Steuer und Formatzeichen wie Leerzeichen "
                "ohne Breite und weiche Trennstriche. Zeilenumbrüche und "
                "Tabulatoren bleiben erhalten."
            ),
            zh="删除不可见的控制和格式字符，例如零宽空格和软连字符。保留换行和制表符。",
        ),
        alias=MultilingualString(
            en="Remove control characters",
            es="Eliminar caracteres de control",
            pt="Remover caracteres de controle",
            de="Steuerzeichen entfernen",
            zh="删除控制字符",
        ),
    )  # type: ignore
    collapse_whitespace: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Turn runs of spaces into one space, remove spaces around line "
                "breaks, keep at most one blank line, and trim the value."
            ),
            es=(
                "Reduce varios espacios seguidos a uno, quita los espacios "
                "alrededor de los saltos de línea, deja como máximo una línea en "
                "blanco y recorta el valor."
            ),
            pt=(
                "Reduz vários espaços seguidos a um, remove espaços ao redor das "
                "quebras de linha, mantém no máximo uma linha em branco e apara "
                "o valor."
            ),
            de=(
                "Fasst mehrere Leerzeichen zu einem zusammen, entfernt "
                "Leerzeichen an Zeilenumbrüchen, behält höchstens eine Leerzeile "
                "und kürzt den Wert an den Rändern."
            ),
            zh=(
                "将连续空格合并为一个，删除换行两侧的空格，最多保留一个空行，并修剪首尾"
                "空白。"
            ),
        ),
        alias=MultilingualString(
            en="Collapse whitespace",
            es="Compactar espacios",
            pt="Compactar espaços",
            de="Leerraum zusammenfassen",
            zh="合并空白",
        ),
    )  # type: ignore


class TextCleaner(BasicPreprocessingConverter, TextValueConverter):
    """Clean the artifacts text extraction leaves in text values.

    Each step can be turned off: Unicode NFKC normalization, rejoining words
    hyphenated across a line break, removing invisible control and format
    characters, and collapsing whitespace while keeping line breaks.
    """

    SCHEMA = TextCleanerSchema
    DISPLAY_NAME = MultilingualString(
        en="Text Cleaner",
        es="Limpiador de Texto",
        pt="Limpador de Texto",
        de="Textbereinigung",
        zh="文本清理器",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Cleans text left by extraction: normalizes Unicode, rejoins "
            "hyphenated words, removes invisible characters and collapses "
            "whitespace."
        ),
        es=(
            "Limpia el texto que deja la extracción: normaliza Unicode, une "
            "palabras con guion, elimina caracteres invisibles y compacta los "
            "espacios."
        ),
        pt=(
            "Limpa o texto deixado pela extração: normaliza Unicode, une "
            "palavras com hífen, remove caracteres invisíveis e compacta os "
            "espaços."
        ),
        de=(
            "Bereinigt Text aus der Extraktion: normalisiert Unicode, verbindet "
            "getrennte Wörter, entfernt unsichtbare Zeichen und fasst Leerraum "
            "zusammen."
        ),
        zh=(
            "清理提取留下的文本：规范化 Unicode、连接连字符拆分的单词、删除不可见字符并"
            "合并空白。"
        ),
    )
    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(
        self,
        normalize_unicode: bool = True,
        join_hyphenated: bool = True,
        remove_control_characters: bool = True,
        collapse_whitespace: bool = True,
    ) -> None:
        """Store which cleaning steps run.

        Parameters
        ----------
        normalize_unicode : bool, optional
            Apply NFKC normalization. Default True.
        join_hyphenated : bool, optional
            Rejoin words hyphenated across a line break. Default True.
        remove_control_characters : bool, optional
            Remove control and format characters except line breaks and
            tabs. Default True.
        collapse_whitespace : bool, optional
            Collapse spaces and blank lines and trim the value. Default True.
        """
        super().__init__()
        self.normalize_unicode = normalize_unicode
        self.join_hyphenated = join_hyphenated
        self.remove_control_characters = remove_control_characters
        self.collapse_whitespace = collapse_whitespace

    def convert_text(self, value: str) -> str:
        """Clean one text value.

        Parameters
        ----------
        value : str
            The value to clean.

        Returns
        -------
        str
            The cleaned value.
        """
        if self.normalize_unicode:
            value = unicodedata.normalize("NFKC", value)
        if self.remove_control_characters:
            value = "".join(
                char
                for char in value
                if char in KEPT_CONTROLS
                or unicodedata.category(char) not in ("Cc", "Cf")
            )
        if self.join_hyphenated:
            value = HYPHEN_BREAK.sub("", value)
        if self.collapse_whitespace:
            value = INLINE_SPACE.sub(" ", value)
            value = SPACE_AT_LINE_EDGE.sub(r"\1", value)
            value = BLANK_LINES.sub(lambda match: match.group(1) * 2, value)
            value = value.strip()
        return value
