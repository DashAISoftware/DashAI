from types import SimpleNamespace

import pyarrow as pa
import pytest

from DashAI.back.converters.document.image_captioning import ImageCaptioningConverter
from DashAI.back.converters.document.language_filter import LanguageFilter
from DashAI.back.converters.document.ocr import OCRConverter
from DashAI.back.converters.hugging_face.pretrained_tool import torch_device
from DashAI.back.converters.hugging_face.summarizer import Summarizer
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
    items_with_details,
)
from DashAI.back.exploration.explorers.named_entities import NamedEntitiesExplorer
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import build_document, image, text

INFO = SimpleNamespace(columns=[{"columnName": "Text"}], name=None, id=3)


class FakeLanguages(LanguageFilter):
    DETECTED = {"Hello there": ("en", 0.9), "Hola": ("es", 0.95), "42": ("en", 0.2)}

    def detect(self, values):
        return [self.DETECTED.get(value, ("fr", 0.99)) for value in values]


class FakeSummaries(Summarizer):
    def summarize(self, values):
        return [f"summary of {len(value.split())} words" for value in values]


class FakeOCR(OCRConverter):
    def read_images(self, images):
        return ["Scanned text " if image.size[0] == 4 else "  " for image in images]


class FakeCaptions(ImageCaptioningConverter):
    def read_images(self, images):
        return ["a red square"] * len(images)


class FakeEntities(NamedEntitiesExplorer):
    def find_entities(self, values):
        return [("Ana", "Person"), ("Ana", "Person"), ("Geneva", "Location")]


def _texts(values):
    table = pa.table({"text": pa.array(values, type=pa.string())})
    return DashAIDataset(table, types={"text": Text(arrow_type=pa.string())})


def test_the_language_filter_keeps_the_chosen_and_uncertain_items():
    document = build_document(["Hello there", "Hola", "Bonjour", "42", "  "])
    converted = apply_converter_to_document(
        document,
        lambda: FakeLanguages(languages=["EN", " es "]),
        {"Text": ItemFilter()},
    )
    assert converted[Text] == ["Hello there", "Hola", "42", "  "]


def test_the_language_filter_can_drop_uncertain_items():
    document = build_document(["Hello there", "42"])
    converted = apply_converter_to_document(
        document,
        lambda: FakeLanguages(languages=["en"], keep_uncertain=False),
        {"Text": ItemFilter()},
    )
    assert converted[Text] == ["Hello there"]


@pytest.mark.parametrize(
    ("languages", "message"),
    [([" "], "at least one"), (["en", "xx"], "Unknown language codes")],
)
def test_bad_languages_are_refused(languages, message):
    with pytest.raises(ValueError, match=message):
        LanguageFilter(languages=languages)


def test_only_long_values_are_summarized():
    data = _texts(["word " * 70, "short one", None])
    result = FakeSummaries(min_words=60).fit(data).transform(data)
    assert result.arrow_table.column("text").to_pylist() == [
        "summary of 70 words",
        "short one",
        None,
    ]


def test_an_empty_summary_keeps_the_value():
    class Blank(Summarizer):
        def summarize(self, values):
            return [" "] * len(values)

    data = _texts(["word " * 70])
    result = Blank(min_words=1).fit(data).transform(data)
    assert result.arrow_table.column("text").to_pylist() == ["word " * 70]


def test_ocr_inserts_the_text_after_the_image_by_default():
    document = build_document(["intro", image(page=2), "outro"])
    converted = apply_converter_to_document(document, FakeOCR, {"Image": ItemFilter()})
    assert [
        (item.type.display_name(), item.kind, item.page, item.content)
        for item in converted.items()
        if item.type is Text
    ] == [
        ("Text", "paragraph", 1, "intro"),
        ("Text", "paragraph", 2, "Scanned text"),
        ("Text", "paragraph", 1, "outro"),
    ]
    assert [item.type.display_name() for item in converted.items()] == [
        "Text",
        "Image",
        "Text",
        "Text",
    ]


def test_ocr_can_replace_images_and_drops_those_without_text():
    class SomeBlank(FakeOCR):
        def read_images(self, images):
            return ["Read", ""][: len(images)]

    document = build_document([image(), image(), "end"])
    converted = apply_converter_to_document(
        document, lambda: SomeBlank(keep_image=False), {"Image": ItemFilter()}
    )
    assert converted.types == [Text]
    assert converted[Text] == ["Read", "end"]


def test_captions_follow_their_images():
    converted = apply_converter_to_document(
        build_document([image(), "body"]), FakeCaptions, {"Image": ItemFilter()}
    )
    assert [(item.type.display_name(), item.kind) for item in converted.items()] == [
        ("Image", "image"),
        ("Text", "caption"),
        ("Text", "paragraph"),
    ]


def test_named_entities_are_counted_in_a_table_and_chart():
    explorer = FakeEntities(top_n=5, min_score=0.5)
    dataset = items_with_details(build_document([text("Ana in Geneva")]), "Text")
    figure = explorer.launch_exploration(dataset, INFO)
    table = figure.data[0]
    assert [list(column) for column in table.cells.values] == [
        ["Ana", "Geneva"],
        ["Person", "Location"],
        [2, 1],
    ]
    assert {trace.name for trace in figure.data[1:]} == {"Location", "Person"}


def test_devices_map_to_torch_names():
    assert torch_device("CPU") == "cpu"
    assert torch_device(None) == "cpu"


@pytest.mark.parametrize(
    ("component", "kinds", "repo"),
    [
        (LanguageFilter, ["document"], "papluca/xlm-roberta-base-language-detection"),
        (Summarizer, ["dataset", "document"], "csebuetnlp/mT5_multilingual_XLSum"),
        (OCRConverter, ["document"], "stepfun-ai/GOT-OCR-2.0-hf"),
        (
            ImageCaptioningConverter,
            ["document"],
            "Salesforce/blip-image-captioning-base",
        ),
        (
            NamedEntitiesExplorer,
            ["dataset", "document"],
            "Davlan/xlm-roberta-base-ner-hrl",
        ),
    ],
)
def test_model_tools_require_a_download(component, kinds, repo):
    metadata = component.get_metadata()
    assert metadata["requires_download"] is True
    assert metadata["download_size_bytes"] > 100_000_000
    assert metadata["data_kinds"] == kinds
    assert component.hf_repos() == [(repo, "model")]


def test_repos_with_safetensors_skip_the_duplicate_bin_weights():
    assert "*.bin" in LanguageFilter.HF_IGNORE_PATTERNS
    assert "*.bin" in NamedEntitiesExplorer.HF_IGNORE_PATTERNS
    assert "*.bin" not in ImageCaptioningConverter.HF_IGNORE_PATTERNS
