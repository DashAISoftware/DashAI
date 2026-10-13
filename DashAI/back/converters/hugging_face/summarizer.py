"""Replace long text values with a summary."""

import re
from typing import Any, List, Optional, Tuple

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
from DashAI.back.core.schema_fields import int_field, schema_field
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.utils import DEVICE_PLACEHOLDER
from DashAI.back.types.value_types import Text

WHITESPACE = re.compile(r"\s+")
BATCH_SIZE = 4
MAX_INPUT_TOKENS = 512


class SummarizerSchema(BaseSchema):
    """Schema for the summarizer."""

    min_words: schema_field(
        int_field(ge=1),
        60,
        description=MultilingualString(
            en=(
                "Values with fewer words are kept as they are; summarizing a "
                "short text does not shorten it."
            ),
            es=(
                "Los valores con menos palabras se conservan tal cual; resumir "
                "un texto corto no lo acorta."
            ),
            pt=(
                "Valores com menos palavras são mantidos como estão; resumir um "
                "texto curto não o encurta."
            ),
            de=(
                "Werte mit weniger Wörtern bleiben unverändert; ein kurzer Text "
                "wird durch Zusammenfassen nicht kürzer."
            ),
            zh="少于此词数的值保持不变；对短文本做摘要不会让它变短。",
        ),
        alias=MultilingualString(
            en="Minimum words to summarize",
            es="Mínimo de palabras para resumir",
            pt="Mínimo de palavras para resumir",
            de="Mindestwörter zum Zusammenfassen",
            zh="触发摘要的最少词数",
        ),
    )  # type: ignore
    max_summary_tokens: schema_field(
        int_field(ge=8, le=512),
        84,
        description=MultilingualString(
            en="Longest summary, in model tokens (about 3/4 of a word each).",
            es=(
                "Resumen más largo, en tokens del modelo (unos 3/4 de palabra cada "
                "uno)."
            ),
            pt="Resumo mais longo, em tokens do modelo (cerca de 3/4 de palavra cada).",
            de="Längste Zusammenfassung in Modell-Tokens (je etwa 3/4 Wort).",
            zh="摘要的最大长度，以模型词元计（每个约 3/4 个单词）。",
        ),
        alias=MultilingualString(
            en="Maximum summary tokens",
            es="Máximo de tokens del resumen",
            pt="Máximo de tokens do resumo",
            de="Maximale Tokens der Zusammenfassung",
            zh="摘要最大词元数",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class Summarizer(AdvancedPreprocessingConverter, PretrainedTool, TextValueConverter):
    """Replace each long text value with an abstractive summary.

    Uses ``csebuetnlp/mT5_multilingual_XLSum``, trained on news in 45
    languages, which writes the summary in the language of the text and
    reads up to 512 tokens. Values shorter than ``min_words`` are kept.
    """

    SCHEMA = SummarizerSchema
    MODEL_NAME = "csebuetnlp/mT5_multilingual_XLSum"
    DOWNLOAD_SIZE_BYTES = 2334026426
    DISPLAY_NAME = MultilingualString(
        en="Summarizer",
        es="Resumidor",
        pt="Resumidor",
        de="Zusammenfasser",
        zh="摘要生成器",
    )
    DESCRIPTION = MultilingualString(
        en="Replaces long texts with a summary in their own language (mT5 XLSum).",
        es=(
            "Reemplaza los textos largos por un resumen en su propio idioma (mT5 "
            "XLSum)."
        ),
        pt="Substitui textos longos por um resumo no próprio idioma (mT5 XLSum).",
        de=(
            "Ersetzt lange Texte durch eine Zusammenfassung in ihrer Sprache (mT5 "
            "XLSum)."
        ),
        zh="将长文本替换为同语言的摘要（mT5 XLSum）。",
    )
    metadata = {
        "allowed_types": [Text],
        "allowed_dtypes": [],
        "data_kinds": [DATASET, DOCUMENT],
    }

    def __init__(
        self,
        min_words: int = 60,
        max_summary_tokens: int = 84,
        device: str = DEVICE_PLACEHOLDER,
    ) -> None:
        """Store the summary options.

        Parameters
        ----------
        min_words : int, optional
            Values with fewer words are kept. Default 60.
        max_summary_tokens : int, optional
            Longest summary in tokens. Default 84.
        device : str, optional
            The device label the model runs on.
        """
        super().__init__()
        self.min_words = min_words
        self.max_summary_tokens = max_summary_tokens
        self.setup_device(device)

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
        model = AutoModelForSeq2SeqLM.from_pretrained(source)
        return tokenizer, model.to(self.device).eval()

    def summarize(self, values: List[str]) -> List[str]:
        """Summarize texts.

        Parameters
        ----------
        values : List[str]
            The texts.

        Returns
        -------
        List[str]
            One summary per text.
        """
        import torch

        tokenizer, model = self.pretrained()
        summaries: List[str] = []
        for batch in batches(
            [WHITESPACE.sub(" ", v).strip() for v in values], BATCH_SIZE
        ):
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_INPUT_TOKENS,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                output = model.generate(
                    **encoded,
                    max_length=self.max_summary_tokens,
                    num_beams=4,
                    no_repeat_ngram_size=2,
                )
            summaries.extend(
                tokenizer.batch_decode(
                    output,
                    skip_special_tokens=True,
                    clean_up_tokenization_spaces=False,
                )
            )
        return summaries

    def convert_texts(self, values: List[Optional[str]]) -> List[Optional[str]]:
        """Summarize the long values of one column and keep the others.

        Parameters
        ----------
        values : List[Optional[str]]
            The column values.

        Returns
        -------
        List[Optional[str]]
            Summaries for the values with at least ``min_words`` words; a
            value whose summary comes out empty is kept.
        """
        long = [
            index
            for index, value in enumerate(values)
            if value is not None and len(value.split()) >= self.min_words
        ]
        result = list(values)
        if long:
            for index, summary in zip(
                long, self.summarize([values[i] for i in long]), strict=True
            ):
                if summary.strip():
                    result[index] = summary.strip()
        return result

    def convert_text(self, value: str) -> str:
        """Summarize one value when it is long enough.

        Parameters
        ----------
        value : str
            The value.

        Returns
        -------
        str
            Its summary, or the value itself when it is short.
        """
        return self.convert_texts([value])[0]
