"""Keep only the document items written in some languages."""

from typing import TYPE_CHECKING, Any, List, Optional, Tuple, Union

from DashAI.back.converters.category.document_processing import (
    DocumentProcessingConverter,
)
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.converters.hugging_face.pretrained_tool import (
    PretrainedTool,
    batches,
    device_field,
)
from DashAI.back.core.schema_fields import (
    bool_field,
    float_field,
    list_field,
    schema_field,
    string_field,
)
from DashAI.back.core.schema_fields.base_schema import BaseSchema
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.downloads.downloadable import HFDownloadableMixin
from DashAI.back.models.utils import DEVICE_PLACEHOLDER
from DashAI.back.types.value_types import Text

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

LANGUAGES = [
    "ar",
    "bg",
    "de",
    "el",
    "en",
    "es",
    "fr",
    "hi",
    "it",
    "ja",
    "nl",
    "pl",
    "pt",
    "ru",
    "sw",
    "th",
    "tr",
    "ur",
    "vi",
    "zh",
]
BATCH_SIZE = 16
MAX_TOKENS = 256


class LanguageFilterSchema(BaseSchema):
    """Schema for the language filter."""

    languages: schema_field(
        list_field(string_field(), min_items=1),
        ["en"],
        description=MultilingualString(
            en=(
                "Language codes of the items to keep, such as 'en' or 'es'. "
                "Known codes: ar, bg, de, el, en, es, fr, hi, it, ja, nl, pl, "
                "pt, ru, sw, th, tr, ur, vi, zh."
            ),
            es=(
                "Códigos de idioma de los elementos a conservar, como 'en' o "
                "'es'. Códigos conocidos: ar, bg, de, el, en, es, fr, hi, it, "
                "ja, nl, pl, pt, ru, sw, th, tr, ur, vi, zh."
            ),
            pt=(
                "Códigos de idioma dos itens a manter, como 'en' ou 'es'. "
                "Códigos conhecidos: ar, bg, de, el, en, es, fr, hi, it, ja, "
                "nl, pl, pt, ru, sw, th, tr, ur, vi, zh."
            ),
            de=(
                "Sprachcodes der zu behaltenden Elemente, etwa 'en' oder 'es'. "
                "Bekannte Codes: ar, bg, de, el, en, es, fr, hi, it, ja, nl, "
                "pl, pt, ru, sw, th, tr, ur, vi, zh."
            ),
            zh=(
                "要保留的元素的语言代码，例如 'en' 或 'es'。可用代码：ar、bg、de、el、"
                "en、es、fr、hi、it、ja、nl、pl、pt、ru、sw、th、tr、ur、vi、zh。"
            ),
        ),
        alias=MultilingualString(
            en="Languages to keep",
            es="Idiomas a conservar",
            pt="Idiomas a manter",
            de="Zu behaltende Sprachen",
            zh="保留的语言",
        ),
    )  # type: ignore
    min_confidence: schema_field(
        float_field(ge=0.0, le=1.0),
        0.5,
        description=MultilingualString(
            en=(
                "Lowest probability, between 0 and 1, for a detected language "
                "to count. Below it the language is uncertain."
            ),
            es=(
                "Probabilidad mínima, entre 0 y 1, para que cuente el idioma "
                "detectado. Por debajo, el idioma es incierto."
            ),
            pt=(
                "Probabilidade mínima, entre 0 e 1, para o idioma detectado "
                "contar. Abaixo dela, o idioma é incerto."
            ),
            de=(
                "Niedrigste Wahrscheinlichkeit zwischen 0 und 1, ab der eine "
                "erkannte Sprache zählt. Darunter ist die Sprache unsicher."
            ),
            zh="检测到的语言被采纳所需的最低概率（0 到 1）。低于此值时语言视为不确定。",
        ),
        alias=MultilingualString(
            en="Minimum confidence",
            es="Confianza mínima",
            pt="Confiança mínima",
            de="Mindestsicherheit",
            zh="最低置信度",
        ),
    )  # type: ignore
    keep_uncertain: schema_field(
        bool_field(),
        True,
        description=MultilingualString(
            en=(
                "Keep items whose language is uncertain, such as numbers, names "
                "or very short text."
            ),
            es=(
                "Conserva los elementos cuyo idioma es incierto, como números, "
                "nombres o textos muy cortos."
            ),
            pt=(
                "Mantém itens cujo idioma é incerto, como números, nomes ou "
                "textos muito curtos."
            ),
            de=(
                "Behält Elemente mit unsicherer Sprache, etwa Zahlen, Namen oder "
                "sehr kurze Texte."
            ),
            zh="保留语言不确定的元素，例如数字、名称或很短的文本。",
        ),
        alias=MultilingualString(
            en="Keep uncertain items",
            es="Conservar inciertos",
            pt="Manter incertos",
            de="Unsichere behalten",
            zh="保留不确定的元素",
        ),
    )  # type: ignore
    device: device_field()  # type: ignore


class LanguageFilter(DocumentProcessingConverter, PretrainedTool, DocumentConverter):
    """Drop the selected Text items written in other languages.

    The language of each item is detected with
    ``papluca/xlm-roberta-base-language-detection``, which knows 20
    languages and reads the first 256 tokens of an item.
    """

    SCHEMA = LanguageFilterSchema
    MODEL_NAME = "papluca/xlm-roberta-base-language-detection"
    HF_IGNORE_PATTERNS = [*HFDownloadableMixin.HF_IGNORE_PATTERNS, "*.bin"]
    DOWNLOAD_SIZE_BYTES = 1126425557
    DISPLAY_NAME = MultilingualString(
        en="Language Filter",
        es="Filtro de Idioma",
        pt="Filtro de Idioma",
        de="Sprachfilter",
        zh="语言过滤器",
    )
    DESCRIPTION = MultilingualString(
        en="Detects the language of each Text item and keeps the chosen ones.",
        es="Detecta el idioma de cada elemento de texto y conserva los elegidos.",
        pt="Detecta o idioma de cada item de texto e mantém os escolhidos.",
        de="Erkennt die Sprache jedes Textelements und behält die gewählten.",
        zh="检测每个文本元素的语言，并保留所选语言的元素。",
    )
    metadata = {"allowed_types": [Text], "allowed_dtypes": []}

    def __init__(
        self,
        languages: Optional[List[str]] = None,
        min_confidence: float = 0.5,
        keep_uncertain: bool = True,
        device: str = DEVICE_PLACEHOLDER,
    ) -> None:
        """Store the languages to keep.

        Parameters
        ----------
        languages : List[str], optional
            Codes of the languages to keep; English when None.
        min_confidence : float, optional
            Lowest probability for a detection to count. Default 0.5.
        keep_uncertain : bool, optional
            Keep items without a confident detection. Default True.
        device : str, optional
            The device label the model runs on.

        Raises
        ------
        ValueError
            If no language is given, or a code is unknown.
        """
        super().__init__()
        codes = [code.strip().lower() for code in (languages or ["en"])]
        codes = [code for code in codes if code]
        if not codes:
            raise ValueError("Choose at least one language to keep.")
        unknown = [code for code in codes if code not in LANGUAGES]
        if unknown:
            raise ValueError(
                f"Unknown language codes {unknown}; known: {', '.join(LANGUAGES)}."
            )
        self.languages = set(codes)
        self.min_confidence = min_confidence
        self.keep_uncertain = keep_uncertain
        self.setup_device(device)

    def load_pretrained(self, source: str) -> Tuple[Any, Any]:
        """Load the tokenizer and the classifier.

        Parameters
        ----------
        source : str
            A local directory or the Hub repo id.

        Returns
        -------
        Tuple[Any, Any]
            The tokenizer and the model, in evaluation mode on the device.
        """
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(source)
        model = AutoModelForSequenceClassification.from_pretrained(source)
        return tokenizer, model.to(self.device).eval()

    def detect(self, values: List[str]) -> List[Tuple[str, float]]:
        """Detect the most likely language of each text.

        Parameters
        ----------
        values : List[str]
            The texts.

        Returns
        -------
        List[Tuple[str, float]]
            ``(code, probability)`` for each text.
        """
        import torch

        tokenizer, model = self.pretrained()
        labels = model.config.id2label
        found: List[Tuple[str, float]] = []
        for batch in batches(values, BATCH_SIZE):
            encoded = tokenizer(
                batch,
                padding=True,
                truncation=True,
                max_length=MAX_TOKENS,
                return_tensors="pt",
            ).to(self.device)
            with torch.no_grad():
                probabilities = model(**encoded).logits.softmax(dim=-1)
            best = probabilities.max(dim=-1)
            found.extend(
                (labels[int(index)], float(probability))
                for probability, index in zip(
                    best.values.tolist(), best.indices.tolist(), strict=True
                )
            )
        return found

    def _keeps(self, value: str, detection: Tuple[str, float]) -> bool:
        """Tell whether an item survives, given its detected language."""
        code, probability = detection
        if not value.strip() or probability < self.min_confidence:
            return self.keep_uncertain
        return code in self.languages

    def transform(
        self, x: "DashAIDataset", y: Union["DashAIDataset", None] = None
    ) -> "DashAIDataset":
        """Return the items in the chosen languages.

        Parameters
        ----------
        x : DashAIDataset
            The selected Text items, in one column.
        y : DashAIDataset, optional
            Ignored.

        Returns
        -------
        DashAIDataset
            The kept items with their source rows.
        """
        values = x.arrow_table.column(0).to_pylist()
        detections = self.detect(values)
        kept = [
            index
            for index, (value, detection) in enumerate(
                zip(values, detections, strict=True)
            )
            if self._keeps(value, detection)
        ]
        return self.items_result([values[index] for index in kept], kept)
