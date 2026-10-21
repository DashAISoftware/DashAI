"""Translate text with a pretrained sequence to sequence model."""

import re
from typing import Any, Dict, List, Optional, Tuple, Union

from DashAI.back.converters.category.advanced_preprocessing import (
    AdvancedPreprocessingConverter,
)
from DashAI.back.converters.hugging_face.pretrained_tool import (
    PretrainedTool,
    batches,
    device_field,
)
from DashAI.back.converters.simple_converters.text_value_converter import (
    TextValueConverter,
)
from DashAI.back.core.data_kinds import DATASET, DOCUMENT
from DashAI.back.core.schema_fields import (
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.utils import DEVICE_PLACEHOLDER
from DashAI.back.types.value_types import Text

WHOLE = "whole"
PARAGRAPHS = "paragraphs"
LINES = "lines"
SENTENCES = "sentences"

PARAGRAPH_BREAK = re.compile(r"(\r?\n[ \t]*(?:\r?\n[ \t]*)+)")
LINE_BREAK = re.compile(r"(\r\n|\r|\n)")
SENTENCE_BREAK = re.compile(r"((?<=[.!?…])\s+|(?<=[。！？])\s*)")
WORD_BREAK = re.compile(r"(\s+)")
EDGE_SPACE = re.compile(r"^(\s*)(.*?)(\s*)$", re.DOTALL)
LETTER = re.compile(r"[^\W\d_]")

FALLBACK_CUTS = [LINE_BREAK, SENTENCE_BREAK]

SPLIT_PATTERNS = {
    WHOLE: [],
    PARAGRAPHS: [PARAGRAPH_BREAK],
    LINES: [LINE_BREAK],
    SENTENCES: [LINE_BREAK, SENTENCE_BREAK],
}

Plan = List[Union[str, int]]

SPLIT_LABELS = {
    WHOLE: MultilingualString(
        en="Whole value",
        es="Valor completo",
        pt="Valor inteiro",
        de="Ganzer Wert",
        zh="整个值",
    ),
    PARAGRAPHS: MultilingualString(
        en="Paragraphs (blank lines)",
        es="Párrafos (líneas en blanco)",
        pt="Parágrafos (linhas em branco)",
        de="Absätze (Leerzeilen)",
        zh="段落（空行分隔）",
    ),
    LINES: MultilingualString(
        en="Lines",
        es="Líneas",
        pt="Linhas",
        de="Zeilen",
        zh="行",
    ),
    SENTENCES: MultilingualString(
        en="Sentences",
        es="Oraciones",
        pt="Frases",
        de="Sätze",
        zh="句子",
    ),
}


def split_keeping_separators(text: str, patterns: List[re.Pattern]) -> List[str]:
    """Cut a text with each pattern in turn, keeping what separates the parts.

    Parameters
    ----------
    text : str
        The text to cut.
    patterns : List[re.Pattern]
        Patterns with one capturing group around the separator, applied
        from the coarsest to the finest.

    Returns
    -------
    List[str]
        Parts at even positions and separators at odd positions; joined,
        they give back ``text`` exactly.
    """
    parts = [text]
    for pattern in patterns:
        finer: List[str] = []
        for index, part in enumerate(parts):
            finer.extend([part] if index % 2 else pattern.split(part))
        parts = finer
    return parts


def language_field(
    labels: Dict[str, MultilingualString], default: str, target: bool
) -> Any:
    """Return the schema field that picks a source or target language.

    Parameters
    ----------
    labels : Dict[str, MultilingualString]
        Model language code to its name, in dropdown order.
    default : str
        The code chosen by default.
    target : bool
        Whether the field picks the language to translate into.

    Returns
    -------
    Any
        A ``source_language`` or ``target_language`` field.
    """
    if target:
        description = MultilingualString(
            en="Language to translate the text into.",
            es="Idioma al que se traduce el texto.",
            pt="Idioma para o qual o texto é traduzido.",
            de="Sprache, in die der Text übersetzt wird.",
            zh="要将文本翻译成的语言。",
        )
        alias = MultilingualString(
            en="Target language",
            es="Idioma de destino",
            pt="Idioma de destino",
            de="Zielsprache",
            zh="目标语言",
        )
    else:
        description = MultilingualString(
            en="Language the text is written in.",
            es="Idioma en el que está escrito el texto.",
            pt="Idioma em que o texto está escrito.",
            de="Sprache, in der der Text geschrieben ist.",
            zh="文本所使用的语言。",
        )
        alias = MultilingualString(
            en="Source language",
            es="Idioma de origen",
            pt="Idioma de origem",
            de="Quellsprache",
            zh="源语言",
        )
    return schema_field(
        enum_field(list(labels), labels=labels),
        default,
        description=description,
        alias=alias,
    )


class TranslationSchema(BaseSchema):
    """Options shared by every translation converter."""

    split_by: schema_field(
        enum_field([WHOLE, PARAGRAPHS, LINES, SENTENCES], labels=SPLIT_LABELS),
        WHOLE,
        description=MultilingualString(
            en=(
                "Translate each value whole, or in parts that keep their line "
                "breaks and spacing. Parts help when one value holds a lot of "
                "text, such as a whole file loaded as a single document item; "
                "values already split by structure do not need them. A part too "
                "long for the model is always cut further, by lines, sentences "
                "and words, so no text is dropped."
            ),
            es=(
                "Traduce cada valor completo, o por partes que conservan sus "
                "saltos de línea y espacios. Las partes sirven cuando un valor "
                "tiene mucho texto, como un archivo completo cargado como un solo "
                "elemento de documento; los valores ya divididos por su estructura "
                "no las necesitan. Una parte demasiado larga para el modelo "
                "siempre se corta más, por líneas, oraciones y palabras, para no "
                "perder texto."
            ),
            pt=(
                "Traduz cada valor inteiro, ou em partes que mantêm suas quebras "
                "de linha e espaços. As partes ajudam quando um valor tem muito "
                "texto, como um arquivo inteiro carregado como um único item de "
                "documento; valores já divididos pela estrutura não precisam "
                "delas. Uma parte longa demais para o modelo é sempre cortada "
                "mais, por linhas, frases e palavras, para não perder texto."
            ),
            de=(
                "Übersetzt jeden Wert als Ganzes oder in Teilen, die ihre "
                "Zeilenumbrüche und Abstände behalten. Teile helfen, wenn ein Wert "
                "viel Text enthält, etwa eine ganze Datei als ein einziges "
                "Dokumentelement; bereits strukturell geteilte Werte brauchen sie "
                "nicht. Ein für das Modell zu langer Teil wird immer weiter nach "
                "Zeilen, Sätzen und Wörtern geteilt, damit kein Text verloren geht."
            ),
            zh=(
                "整体翻译每个值，或按保留换行和空格的部分翻译。当一个值包含大量"
                "文本时（例如作为单个文档元素加载的整个文件），分部分翻译很有用；"
                "已按结构拆分的值则不需要。对模型来说过长的部分总会按行、句子和"
                "单词进一步切分，因此不会丢失文本。"
            ),
        ),
        alias=MultilingualString(
            en="Translate by",
            es="Traducir por",
            pt="Traduzir por",
            de="Übersetzen nach",
            zh="翻译单位",
        ),
    )  # type: ignore
    batch_size: schema_field(
        int_field(ge=1),
        8,
        description=MultilingualString(
            en="Number of texts translated together. Lower it if memory runs out.",
            es="Cantidad de textos traducidos juntos. Bájala si falta memoria.",
            pt="Quantidade de textos traduzidos juntos. Diminua se faltar memória.",
            de=(
                "Anzahl gemeinsam übersetzter Texte. Verringern, wenn der "
                "Speicher nicht reicht."
            ),
            zh="一次翻译的文本数量。内存不足时请调低。",
        ),
        alias=MultilingualString(
            en="Batch size",
            es="Tamaño de lote",
            pt="Tamanho do lote",
            de="Batchgröße",
            zh="批大小",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class TranslationConverter(
    AdvancedPreprocessingConverter, PretrainedTool, TextValueConverter
):
    """Translate every text value with one pretrained translation model.

    Subclasses set ``MODEL_NAME`` and ``DOWNLOAD_SIZE_BYTES`` and, for models
    that need them, the language hooks :meth:`source_prefix`,
    :meth:`prepare_tokenizer` and :meth:`generate_options`. Values without
    letters are kept, and the spacing around every translated piece is kept
    as it was. A piece longer than ``MAX_INPUT_TOKENS`` is cut by lines,
    then sentences, then words: translation models are trained on single
    sentences and skip content of long inputs.
    """

    SCHEMA = TranslationSchema
    MAX_INPUT_TOKENS = 128
    MAX_OUTPUT_TOKENS = 512
    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(
        self,
        split_by: str = WHOLE,
        batch_size: int = 8,
        device: str = DEVICE_PLACEHOLDER,
    ) -> None:
        """Store the translation options.

        Parameters
        ----------
        split_by : str, optional
            ``"whole"``, ``"paragraphs"``, ``"lines"`` or ``"sentences"``.
            Default ``"whole"``.
        batch_size : int, optional
            Texts translated together. Default 8.
        device : str, optional
            The device label the model runs on.

        Raises
        ------
        ValueError
            If ``split_by`` is not one of the options.
        """
        super().__init__()
        if split_by not in SPLIT_PATTERNS:
            raise ValueError(f"Unknown split_by '{split_by}'.")
        self.split_by = split_by
        self.batch_size = batch_size
        self.setup_device(device)

    def source_prefix(self) -> str:
        """Return the text the model expects in front of every input.

        Returns
        -------
        str
            Empty by default.
        """
        return ""

    def prepare_tokenizer(self, tokenizer: Any) -> None:
        """Set up the tokenizer for the source language.

        Parameters
        ----------
        tokenizer : Any
            The loaded tokenizer.
        """

    def generate_options(self, tokenizer: Any) -> Dict[str, Any]:
        """Return extra ``generate`` arguments, such as the target language.

        Parameters
        ----------
        tokenizer : Any
            The loaded tokenizer.

        Returns
        -------
        Dict[str, Any]
            Empty by default.
        """
        return {}

    def load_pretrained(self, source: str) -> Tuple[Any, Any]:
        """Load the tokenizer and the sequence to sequence model.

        Parameters
        ----------
        source : str
            A local directory or the Hub repo id.

        Returns
        -------
        Tuple[Any, Any]
            The tokenizer and the model, in evaluation mode on the device.
        """
        from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(source)
        self.prepare_tokenizer(tokenizer)
        model = AutoModelForSeq2SeqLM.from_pretrained(source)
        return tokenizer, model.to(self.device).eval()

    def count_tokens(self, text: str) -> int:
        """Count the tokens the model reads for a text.

        Parameters
        ----------
        text : str
            The text.

        Returns
        -------
        int
            Its token count, without special tokens.
        """
        tokenizer, _ = self.pretrained()
        return len(tokenizer(text, add_special_tokens=False)["input_ids"])

    def translate_pieces(self, pieces: List[str]) -> List[str]:
        """Translate short texts, each fitting the model input.

        Pieces are batched by length so that a batch pads little.

        Parameters
        ----------
        pieces : List[str]
            The texts.

        Returns
        -------
        List[str]
            One translation per text, in the same order.
        """
        import torch

        tokenizer, model = self.pretrained()
        prefix = self.source_prefix()
        options = self.generate_options(tokenizer)
        order = sorted(range(len(pieces)), key=lambda index: len(pieces[index]))
        translations: List[str] = [""] * len(pieces)
        for batch in batches(order, self.batch_size):
            encoded = tokenizer(
                [prefix + pieces[index] for index in batch],
                padding=True,
                truncation=True,
                return_tensors="pt",
            ).to(self.device)
            longest = encoded["input_ids"].shape[1]
            with torch.no_grad():
                output = model.generate(
                    **encoded,
                    max_new_tokens=min(self.MAX_OUTPUT_TOKENS, 3 * longest + 16),
                    **options,
                )
            decoded = tokenizer.batch_decode(output, skip_special_tokens=True)
            for index, text in zip(batch, decoded, strict=True):
                translations[index] = text.strip()
        return translations

    def _queue(self, text: str, pending: List[str]) -> int:
        """Queue a piece for the model.

        Parameters
        ----------
        text : str
            The piece.
        pending : List[str]
            Pieces queued so far; ``text`` is appended.

        Returns
        -------
        int
            Its position in ``pending``.
        """
        pending.append(text)
        return len(pending) - 1

    def _fit(self, text: str, pending: List[str], depth: int = 0) -> Plan:
        """Plan a part so that every queued piece fits the model input.

        A part that fits is one piece. A longer one is cut into lines and
        then into sentences, each translated on its own: the model drops
        line breaks inside a piece and skips content of long inputs. A
        sentence that is still too long is cut between words.

        Parameters
        ----------
        text : str
            The part.
        pending : List[str]
            Pieces queued for the model; new pieces are appended.
        depth : int, optional
            Position in ``FALLBACK_CUTS`` of the next cut to try.

        Returns
        -------
        Plan
            Kept strings and positions of queued pieces, in text order.
        """
        lead, core, trail = EDGE_SPACE.match(text).groups()
        if not LETTER.search(core):
            return [text]
        if self.count_tokens(core) <= self.MAX_INPUT_TOKENS:
            return [lead, self._queue(core, pending), trail]
        for level in range(depth, len(FALLBACK_CUTS)):
            parts = FALLBACK_CUTS[level].split(core)
            if len(parts) > 1:
                plan: Plan = [lead]
                for index, part in enumerate(parts):
                    plan.extend(
                        [part] if index % 2 else self._fit(part, pending, level + 1)
                    )
                return [*plan, trail]
        return [lead, *self._pack_words(core, pending), trail]

    def _pack_words(self, text: str, pending: List[str]) -> Plan:
        """Cut a long sentence between words into pieces that fit.

        Consecutive words are joined while they fit the model input; a
        single word longer than the limit is cut into character slices.

        Parameters
        ----------
        text : str
            The sentence, without surrounding whitespace.
        pending : List[str]
            Pieces queued for the model; new pieces are appended.

        Returns
        -------
        Plan
            Kept spaces and positions of queued pieces, in text order.
        """
        parts = WORD_BREAK.split(text)
        plan: Plan = []
        current = ""
        gap = ""
        for index in range(0, len(parts), 2):
            word = parts[index]
            separator = parts[index + 1] if index + 1 < len(parts) else ""
            if current:
                joined = f"{current}{gap}{word}"
                if self.count_tokens(joined) <= self.MAX_INPUT_TOKENS:
                    current, gap = joined, separator
                    continue
                plan.extend([self._queue(current, pending), gap])
            tokens = self.count_tokens(word)
            if tokens <= self.MAX_INPUT_TOKENS:
                current, gap = word, separator
                continue
            size = max(1, len(word) * self.MAX_INPUT_TOKENS // tokens)
            plan.extend(
                self._queue(word[start : start + size], pending)
                for start in range(0, len(word), size)
            )
            plan.append(separator)
            current, gap = "", ""
        if current:
            plan.extend([self._queue(current, pending), gap])
        return plan

    def _plan(self, text: str, pending: List[str]) -> Plan:
        """Plan the translation of one value.

        Parameters
        ----------
        text : str
            The value.
        pending : List[str]
            Pieces queued for the model; new pieces are appended.

        Returns
        -------
        Plan
            Kept strings and positions of queued pieces, in text order.
        """
        parts = split_keeping_separators(text, SPLIT_PATTERNS[self.split_by])
        plan: Plan = []
        for index, part in enumerate(parts):
            plan.extend([part] if index % 2 else self._fit(part, pending))
        return plan

    def convert_texts(self, values: List[Optional[str]]) -> List[Optional[str]]:
        """Translate the values of one column in a single model run.

        Parameters
        ----------
        values : List[Optional[str]]
            The column values.

        Returns
        -------
        List[Optional[str]]
            The translations; missing values and values without letters
            are kept.
        """
        pending: List[str] = []
        plans = [
            self._plan(value, pending)
            if value is not None and LETTER.search(value)
            else None
            for value in values
        ]
        outputs = self.translate_pieces(pending) if pending else []
        return [
            value
            if plan is None
            else "".join(
                part if isinstance(part, str) else outputs[part] for part in plan
            )
            for value, plan in zip(values, plans, strict=True)
        ]

    def convert_text(self, value: str) -> str:
        """Translate one value.

        Parameters
        ----------
        value : str
            The value.

        Returns
        -------
        str
            Its translation.
        """
        return self.convert_texts([value])[0]
