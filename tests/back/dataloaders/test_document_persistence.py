import json

import pytest

from DashAI.back.dataloaders.classes.dashai_document import (
    DashAIDocument,
    DocumentItem,
    load_document,
    save_document,
)
from DashAI.back.types.dashai_image import DashAIImage
from DashAI.back.types.value_types import Text

PNG_BYTES = b"\x89PNG\r\n\x1a\nfake"


def _document():
    return DashAIDocument.from_items(
        [
            DocumentItem(Text, "Résumé del capítulo 1", page=1),
            DocumentItem(
                DashAIImage, DashAIImage(bytes=PNG_BYTES, path="f.png"), page=1
            ),
            DocumentItem(Text, "第二页"),
        ],
        metadata={"file_name": "doc.pdf", "file_type": "pdf", "n_pages": 2},
    )


def test_round_trip_keeps_contents_order_and_metadata(tmp_path):
    save_document(_document(), tmp_path / "doc")

    loaded = load_document(tmp_path / "doc")

    assert loaded[Text] == ["Résumé del capítulo 1", "第二页"]
    assert loaded[DashAIImage][0].bytes == PNG_BYTES
    assert [(i.type, i.position, i.page) for i in loaded.items()] == [
        (Text, 0, 1),
        (DashAIImage, 1, 1),
        (Text, 2, None),
    ]
    assert loaded.metadata == {"file_name": "doc.pdf", "file_type": "pdf", "n_pages": 2}


def test_interleaved_order_survives_round_trip(tmp_path):
    order = [Text, DashAIImage, Text, DashAIImage, DashAIImage, Text]
    items = [
        DocumentItem(Text, f"t{i}")
        if content_type is Text
        else DocumentItem(DashAIImage, DashAIImage(bytes=PNG_BYTES, path=f"i{i}.png"))
        for i, content_type in enumerate(order)
    ]
    save_document(DashAIDocument.from_items(items), tmp_path / "doc")

    loaded = load_document(tmp_path / "doc").items()

    assert [item.type for item in loaded] == order
    assert [
        item.content if item.type is Text else item.content.path for item in loaded
    ] == ["t0", "i1.png", "t2", "i3.png", "i4.png", "t5"]


def test_files_on_disk(tmp_path):
    save_document(_document(), tmp_path / "doc")

    assert sorted(p.name for p in (tmp_path / "doc").iterdir()) == [
        "document.json",
        "image.arrow",
        "text.arrow",
    ]
    sidecar = json.loads((tmp_path / "doc" / "document.json").read_text("utf-8"))
    assert sidecar["version"] == 1
    assert sidecar["content_counts"] == {"Text": 2, "Image": 1}


def test_text_only_document_writes_no_image_file(tmp_path):
    document = DashAIDocument.from_items([DocumentItem(Text, "only text")])

    save_document(document, tmp_path / "doc")
    loaded = load_document(tmp_path / "doc")

    assert not (tmp_path / "doc" / "image.arrow").exists()
    assert loaded[DashAIImage] == []
    assert loaded.types == [Text]


def test_overwrite_removes_stale_type_files(tmp_path):
    save_document(_document(), tmp_path / "doc")
    text_only = DashAIDocument.from_items([DocumentItem(Text, "new version")])

    save_document(text_only, tmp_path / "doc")

    assert not (tmp_path / "doc" / "image.arrow").exists()
    assert load_document(tmp_path / "doc")[Text] == ["new version"]


def test_loaded_text_table_keeps_dashai_types(tmp_path):
    save_document(_document(), tmp_path / "doc")

    dataset = load_document(tmp_path / "doc").as_dataset(Text)

    assert dataset.types["content"].to_string()["type"] == "Text"


def test_empty_document_round_trip(tmp_path):
    save_document(DashAIDocument.from_items([]), tmp_path / "doc")

    assert load_document(tmp_path / "doc").items() == []


def test_load_missing_document_raises(tmp_path):
    with pytest.raises(FileNotFoundError, match="document.json"):
        load_document(tmp_path / "nothing")
