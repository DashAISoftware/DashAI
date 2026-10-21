"""Replace or redact the parts of text values that match a pattern."""

import re
from typing import Optional

from DashAI.back.converters.category.basic_preprocessing import (
    BasicPreprocessingConverter,
)
from DashAI.back.converters.simple_converters.text_value_converter import (
    TextValueConverter,
)
from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.schema_fields import (
    bool_field,
    enum_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.types.value_types import Text

CUSTOM = "Custom pattern"
EMPTY_MATCH_PROBE = "Ab 1.\n"
PRESETS = {
    "Email addresses": r"[\w.+-]+@[\w-]+(?:\.[\w-]+)+",
    "URLs": r"(?:https?://|www\.)[^\s<>\"']+",
    "Phone numbers": r"(?<!\w)\+?\d[\d ().-]{6,}\d(?!\w)",
    "Numbers": r"(?<!\w)\d+(?:[.,]\d+)*(?!\w)",
}


class RegexReplacerSchema(BaseSchema):
    """Schema for the regex replacer."""

    preset: schema_field(
        enum_field([CUSTOM, *PRESETS]),
        CUSTOM,
        description=MultilingualString(
            en=(
                "What to find. Pick a preset to redact emails, URLs, phone "
                "numbers or numbers, or 'Custom pattern' to use your own "
                "regular expression."
            ),
            es=(
                "Qué buscar. Elige un preajuste para ocultar correos, URLs, "
                "teléfonos o números, o 'Custom pattern' para usar tu propia "
                "expresión regular."
            ),
            pt=(
                "O que procurar. Escolha uma predefinição para ocultar emails, "
                "URLs, telefones ou números, ou 'Custom pattern' para usar sua "
                "própria expressão regular."
            ),
            de=(
                "Was gesucht wird. Eine Vorgabe schwärzt E-Mails, URLs, "
                "Telefonnummern oder Zahlen; 'Custom pattern' nutzt einen "
                "eigenen regulären Ausdruck."
            ),
            zh=(
                "要查找的内容。选择预设以隐藏邮箱、URL、电话号码或数字，或选择 'Custom "
                "pattern' 使用自定义正则表达式。"
            ),
        ),
        alias=MultilingualString(
            en="Find",
            es="Buscar",
            pt="Procurar",
            de="Suchen",
            zh="查找",
        ),
    )  # type: ignore
    pattern: schema_field(
        none_type(string_field()),
        None,
        description=MultilingualString(
            en=(
                "Regular expression (Python syntax) used with 'Custom pattern'. "
                "Ignored for the presets."
            ),
            es=(
                "Expresión regular (sintaxis de Python) usada con 'Custom "
                "pattern'. Se ignora en los preajustes."
            ),
            pt=(
                "Expressão regular (sintaxe Python) usada com 'Custom pattern'. "
                "Ignorada nas predefinições."
            ),
            de=(
                "Regulärer Ausdruck (Python Syntax) für 'Custom pattern'. Bei "
                "den Vorgaben ignoriert."
            ),
            zh="与 'Custom pattern' 一起使用的正则表达式（Python 语法）。预设时忽略。",
        ),
        alias=MultilingualString(
            en="Pattern",
            es="Patrón",
            pt="Padrão",
            de="Muster",
            zh="模式",
        ),
    )  # type: ignore
    replacement: schema_field(
        string_field(),
        "",
        description=MultilingualString(
            en=(
                "Text that replaces each match, such as '[EMAIL]'. Empty removes "
                "the matches. With a custom pattern, \\1 inserts the first group."
            ),
            es=(
                "Texto que reemplaza cada coincidencia, como '[EMAIL]'. Vacío "
                "elimina las coincidencias. Con un patrón propio, \\1 inserta el "
                "primer grupo."
            ),
            pt=(
                "Texto que substitui cada ocorrência, como '[EMAIL]'. Vazio "
                "remove as ocorrências. Com um padrão próprio, \\1 insere o "
                "primeiro grupo."
            ),
            de=(
                "Text, der jeden Treffer ersetzt, etwa '[EMAIL]'. Leer entfernt "
                "die Treffer. Bei eigenem Muster fügt \\1 die erste Gruppe ein."
            ),
            zh=(
                "替换每个匹配项的文本，例如 '[EMAIL]'。为空时删除匹配项。使用自定义模式"
                "时，\\1 插入第一个分组。"
            ),
        ),
        alias=MultilingualString(
            en="Replace with",
            es="Reemplazar por",
            pt="Substituir por",
            de="Ersetzen durch",
            zh="替换为",
        ),
    )  # type: ignore
    ignore_case: schema_field(
        bool_field(),
        False,
        description=MultilingualString(
            en="Match upper and lower case letters alike.",
            es="Coincide sin distinguir mayúsculas y minúsculas.",
            pt="Corresponde sem distinguir maiúsculas e minúsculas.",
            de="Groß und Kleinschreibung nicht unterscheiden.",
            zh="匹配时不区分大小写。",
        ),
        alias=MultilingualString(
            en="Ignore case",
            es="Ignorar mayúsculas",
            pt="Ignorar maiúsculas",
            de="Groß/Klein ignorieren",
            zh="忽略大小写",
        ),
    )  # type: ignore


class RegexReplacer(BasicPreprocessingConverter, TextValueConverter):
    """Replace every match of a regular expression in text values.

    Presets redact email addresses, URLs, phone numbers or numbers; a custom
    pattern accepts any Python regular expression, and its replacement may
    use group references such as ``\\1``.
    """

    SCHEMA = RegexReplacerSchema
    DISPLAY_NAME = MultilingualString(
        en="Regex Replace / Redact",
        es="Reemplazo / Ocultación con Regex",
        pt="Substituição / Ocultação com Regex",
        de="Regex Ersetzen / Schwärzen",
        zh="正则替换 / 脱敏",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Replaces the parts of text that match a regular expression, with "
            "presets to redact emails, URLs, phone numbers and numbers."
        ),
        es=(
            "Reemplaza las partes del texto que coinciden con una expresión "
            "regular, con preajustes para ocultar correos, URLs, teléfonos y "
            "números."
        ),
        pt=(
            "Substitui as partes do texto que correspondem a uma expressão "
            "regular, com predefinições para ocultar emails, URLs, telefones e "
            "números."
        ),
        de=(
            "Ersetzt Textstellen, die einem regulären Ausdruck entsprechen, mit "
            "Vorgaben zum Schwärzen von E-Mails, URLs, Telefonnummern und Zahlen."
        ),
        zh=(
            "替换与正则表达式匹配的文本部分，并提供隐藏邮箱、URL、电话号码和数字的预设"
            "。"
        ),
    )
    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(
        self,
        preset: str = CUSTOM,
        pattern: Optional[str] = None,
        replacement: str = "",
        ignore_case: bool = False,
    ) -> None:
        """Compile the pattern to replace.

        Parameters
        ----------
        preset : str, optional
            A key of ``PRESETS``, or ``"Custom pattern"`` to use ``pattern``.
        pattern : str, optional
            The custom regular expression.
        replacement : str, optional
            Replacement for each match; empty removes the matches.
        ignore_case : bool, optional
            Match without regard to case. Default False.

        Raises
        ------
        ValueError
            If the preset is unknown, the custom pattern is missing or empty,
            the pattern does not compile, or it matches the empty string.
            A replacement that refers to a missing group is refused when the
            first match is replaced.
        """
        super().__init__()
        if preset == CUSTOM:
            if not pattern:
                raise ValueError("Write a pattern to use 'Custom pattern'.")
            source = pattern
        elif preset in PRESETS:
            source = PRESETS[preset]
        else:
            raise ValueError(f"Unknown preset {preset!r}.")
        try:
            self.regex = re.compile(source, re.IGNORECASE if ignore_case else 0)
        except re.error as e:
            raise ValueError(f"The pattern {source!r} is not valid: {e}.") from e
        if self.regex.fullmatch("") or any(
            match.group(0) == "" for match in self.regex.finditer(EMPTY_MATCH_PROBE)
        ):
            raise ValueError(
                f"The pattern {source!r} matches empty text, so it would insert "
                "the replacement everywhere."
            )
        self.replacement = replacement or ""

    def convert_text(self, value: str) -> str:
        """Replace every match in one text value.

        Parameters
        ----------
        value : str
            The value to rewrite.

        Returns
        -------
        str
            The value with every match replaced.

        Raises
        ------
        ValueError
            If the replacement refers to a group the pattern does not have.
        """
        try:
            return self.regex.sub(self.replacement, value)
        except (re.error, IndexError) as e:
            raise ValueError(
                f"The replacement {self.replacement!r} is not valid: {e}."
            ) from e
