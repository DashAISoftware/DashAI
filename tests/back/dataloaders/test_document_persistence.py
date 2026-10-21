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
    assert sidecar["version"] == 2
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


def test_load_rejects_missing_type_file(tmp_path):
    save_document(_document(), tmp_path / "doc")
    (tmp_path / "doc" / "image.arrow").unlink()

    with pytest.raises(FileNotFoundError, match="image.arrow"):
        load_document(tmp_path / "doc")


def test_load_rejects_count_mismatch(tmp_path):
    save_document(_document(), tmp_path / "doc")
    sidecar_path = tmp_path / "doc" / "document.json"
    sidecar = json.loads(sidecar_path.read_text("utf-8"))
    sidecar["content_counts"]["Text"] = 5
    sidecar_path.write_text(json.dumps(sidecar), "utf-8")

    with pytest.raises(ValueError, match="expected 5"):
        load_document(tmp_path / "doc")


def test_load_rejects_unknown_version(tmp_path):
    save_document(_document(), tmp_path / "doc")
    sidecar_path = tmp_path / "doc" / "document.json"
    sidecar = json.loads(sidecar_path.read_text("utf-8"))
    sidecar["version"] = 99
    sidecar_path.write_text(json.dumps(sidecar), "utf-8")

    with pytest.raises(ValueError, match="version"):
        load_document(tmp_path / "doc")


def test_kinds_and_attrs_survive_a_round_trip(tmp_path):
    items = [
        DocumentItem(Text, "Title", kind="title"),
        DocumentItem(Text, "Step one", kind="list_item", attrs={"ordered": True}),
        DocumentItem(DashAIImage, DashAIImage(bytes=PNG_BYTES, path="f.png")),
        DocumentItem(Text, "x = 1", kind="code", attrs={"language": "python"}),
    ]
    save_document(DashAIDocument.from_items(items), tmp_path / "doc")

    loaded = load_document(tmp_path / "doc").items()

    assert [(item.kind, item.attrs) for item in loaded] == [
        ("title", {}),
        ("list_item", {"ordered": True, "depth": 0}),
        ("image", {}),
        ("code", {"language": "python"}),
    ]


def test_version_1_documents_load_as_paragraphs_and_images(tmp_path):
    import pyarrow as pa

    save_document(_document(), tmp_path / "doc")
    directory = tmp_path / "doc"
    for name in ("text.arrow", "image.arrow"):
        path = directory / name
        with pa.OSFile(str(path), "rb") as source:
            table = pa.ipc.open_file(source).read_all()
        old = table.drop_columns(["kind", "attrs"])
        with pa.OSFile(str(path), "wb") as sink:
            writer = pa.ipc.new_file(sink, old.schema)
            writer.write_table(old)
            writer.close()
    sidecar_path = directory / "document.json"
    sidecar = json.loads(sidecar_path.read_text("utf-8"))
    sidecar["version"] = 1
    sidecar_path.write_text(json.dumps(sidecar), "utf-8")

    loaded = load_document(directory)

    assert [(item.type, item.kind, item.attrs) for item in loaded.items()] == [
        (Text, "paragraph", {}),
        (DashAIImage, "image", {}),
        (Text, "paragraph", {}),
    ]
    assert loaded[Text] == ["Résumé del capítulo 1", "第二页"]


def test_read_content_columns_include_kind_and_attrs(tmp_path):
    from DashAI.back.dataloaders.classes.dashai_document import read_content_columns

    items = [
        DocumentItem(Text, "H", kind="heading", attrs={"level": 1}),
        DocumentItem(DashAIImage, DashAIImage(bytes=PNG_BYTES, path="f.png")),
    ]
    save_document(DashAIDocument.from_items(items), tmp_path / "doc")

    texts = read_content_columns(tmp_path / "doc", Text)
    images = read_content_columns(tmp_path / "doc", DashAIImage, with_content=False)

    assert texts["kind"] == ["heading"]
    assert texts["attrs"] == [{"level": 1}]
    assert images["kind"] == ["image"]
    assert images["attrs"] == [{}]
    assert "content" not in images
