import os
import shutil
from types import SimpleNamespace

import pytest

from DashAI.back.dataloaders.classes.dashai_document import (
    load_document,
    save_document,
)
from DashAI.back.dataloaders.classes.document_items import (
    ItemFilter,
    apply_converter_to_document,
)
from DashAI.back.dataloaders.classes.notebook_data import (
    get_notebook_columns_spec,
    load_explorer_input,
    notebook_data_path,
    restore_notebook_data,
)
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import image, text, write_document


def _document_notebook(tmp_path, items):
    stored = tmp_path / "stored"
    write_document(stored / "document", items)
    working = tmp_path / "notebook"
    shutil.copytree(stored / "document", working / "document")
    return SimpleNamespace(
        data_kind="document",
        file_path=str(working),
        document=SimpleNamespace(file_path=str(stored)),
        dataset=None,
    )


class _Changed:
    """A converter that replaces every value with ``changed``."""

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

        table = pa.table({"Text": pa.array(["changed"] * len(x), type=pa.string())})
        return DashAIDataset(table, types={"Text": Text(arrow_type=pa.string())})


def test_document_notebooks_keep_their_data_in_a_document_folder(tmp_path):
    notebook = _document_notebook(tmp_path, ["a"])
    assert notebook_data_path(notebook) == os.path.join(notebook.file_path, "document")


def test_dataset_notebooks_keep_their_data_in_a_dataset_folder():
    notebook = SimpleNamespace(data_kind="dataset", file_path="nb")
    assert notebook_data_path(notebook) == os.path.join("nb", "dataset")


def test_the_document_columns_spec_comes_from_the_working_copy(tmp_path):
    notebook = _document_notebook(tmp_path, ["a", "b", image()])
    spec = get_notebook_columns_spec(notebook)
    assert set(spec) == {"Text", "Image"}
    assert spec["Text"]["count"] == 2


def test_restore_brings_back_the_original_document(tmp_path):
    notebook = _document_notebook(tmp_path, ["hello"])
    working = notebook_data_path(notebook)
    document = load_document(working)
    save_document(
        apply_converter_to_document(document, _Changed, {"Text": ItemFilter()}), working
    )
    assert load_document(working)[Text] == ["changed"]

    restore_notebook_data(notebook)

    assert load_document(working)[Text] == ["hello"]


def test_explorer_input_for_a_document_is_the_content_and_item_columns(tmp_path):
    notebook = _document_notebook(
        tmp_path, [text("Title", kind="title"), "a", text("b", page=2), image()]
    )
    dataset = load_explorer_input(
        notebook, [{"columnName": "Text", "kinds": ["paragraph"]}]
    )
    assert dataset.column_names == ["Text", "kind", "page", "position"]
    assert dataset.arrow_table.to_pydict() == {
        "Text": ["a", "b"],
        "kind": ["paragraph", "paragraph"],
        "page": [1, 2],
        "position": [1, 2],
    }
    assert dataset.types["page"].to_string()["type"] == "Integer"


def test_the_base_explorer_keeps_only_the_selected_content(tmp_path):
    from DashAI.back.exploration.explorers.wordcloud import WordcloudExplorer

    notebook = _document_notebook(tmp_path, ["a"])
    columns = [{"columnName": "Text"}]
    dataset = load_explorer_input(notebook, columns)
    prepared = WordcloudExplorer().prepare_dataset(dataset, columns)
    assert prepared.column_names == ["Text"]


def test_explorer_input_refuses_two_content_types(tmp_path):
    notebook = _document_notebook(tmp_path, ["a", image()])
    with pytest.raises(ValueError, match="exactly one"):
        load_explorer_input(notebook, [{"columnName": "Text"}, {"columnName": "Image"}])
