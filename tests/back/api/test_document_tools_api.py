"""Explorers, validation and data endpoints of document notebooks."""

import pyarrow as pa
import pytest
from fastapi.testclient import TestClient

from DashAI.back.converters.base_converter import BaseConverter, BaseConverterSchema
from DashAI.back.converters.document_converter import DocumentConverter
from DashAI.back.core.data_kinds import DOCUMENT
from DashAI.back.core.enums.status import ExplorerStatus
from DashAI.back.dataloaders.classes.dashai_dataset import get_columns_spec
from DashAI.back.dependencies.database.models import Dataset, Explorer
from DashAI.back.job.explorer_job import ExplorerJob
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import create_document_notebook, image, text

REPLACE = {"char_to_replace": "a", "replacement_char": "b"}
WORDS = {"max_words": 20, "background_color": None}
DESCRIBE = {"percentiles": None, "include": None, "exclude": None}
ITEMS = [
    text("Report", kind="title"),
    "alpha beta gamma",
    image(),
    text("Results", kind="heading", page=2, level=2),
    "beta gamma",
]


@pytest.fixture(scope="module", name="document_notebook_id")
def fixture_document_notebook_id(client: TestClient) -> int:
    return create_document_notebook(client, "tools_document", ITEMS)


@pytest.fixture(scope="module", name="dataset_notebook_id")
def fixture_dataset_notebook_id(client: TestClient, dataset_1: Dataset) -> int:
    response = client.post(
        "/api/v1/notebook/",
        json={"name": "tools_dataset", "dataset_id": dataset_1.id},
    )
    assert response.status_code == 201, response.text
    return response.json()["id"]


def _post_converter(client, notebook_id, name, params, columns, target=None):
    return client.post(
        "/api/v1/converter/",
        json={
            "notebook_id": notebook_id,
            "converter": name,
            "parameters": {
                "order": 1,
                "params": params,
                "scope": {
                    "columns": [
                        {"idx": index + 1, **column}
                        for index, column in enumerate(columns)
                    ],
                    "rows": [],
                },
                "target": target,
            },
        },
    )


def _post_explorer(client, notebook_id, name, columns, parameters):
    return client.post(
        "/api/v1/explorer/",
        json={
            "notebook_id": notebook_id,
            "exploration_type": name,
            "columns": columns,
            "parameters": parameters,
            "name": name,
        },
    )


def test_document_columns_are_content_types_with_kinds(
    client: TestClient, document_notebook_id: int
):
    response = client.get(f"/api/v1/notebook/{document_notebook_id}/columns")

    assert response.status_code == 200, response.text
    assert response.json() == {
        "Text": {
            "type": "Text",
            "dtype": "string",
            "count": 4,
            "kinds": {"title": 1, "paragraph": 2, "heading": 1},
        },
        "Image": {
            "type": "Image",
            "dtype": "struct",
            "count": 1,
            "kinds": {"image": 1},
        },
    }


def test_dataset_notebook_columns_match_the_dataset(
    client: TestClient, dataset_notebook_id: int
):
    notebook = client.get(f"/api/v1/notebook/{dataset_notebook_id}").json()
    response = client.get(f"/api/v1/notebook/{dataset_notebook_id}/columns")
    assert response.status_code == 200, response.text
    assert response.json() == get_columns_spec(f"{notebook['file_path']}/dataset")


def test_an_unknown_notebook_has_no_columns(client: TestClient):
    assert client.get("/api/v1/notebook/999999/columns").status_code == 404


def test_document_content_filters_by_kind(
    client: TestClient, document_notebook_id: int
):
    response = client.get(
        f"/api/v1/notebook/{document_notebook_id}/document-content",
        params={"kind": ["title", "heading"]},
    )
    body = response.json()
    assert body["total"] == 2
    assert [item["content"] for item in body["items"]] == ["Report", "Results"]


@pytest.mark.parametrize(
    "columns",
    [
        [{"columnName": "Text"}],
        [{"columnName": "Text", "kinds": ["paragraph", "heading"]}],
    ],
)
def test_a_document_converter_is_accepted_on_text_items(
    client, document_notebook_id, columns
):
    response = _post_converter(
        client, document_notebook_id, "CharacterReplacer", REPLACE, columns
    )
    assert response.status_code == 201, response.text


def test_a_datasets_only_converter_is_refused_on_documents(
    client, document_notebook_id
):
    response = _post_converter(
        client,
        document_notebook_id,
        "BagOfWordsConverter",
        {},
        [{"columnName": "Text"}],
    )
    assert response.status_code == 422, response.text


def test_a_text_converter_is_refused_on_images(client, document_notebook_id):
    response = _post_converter(
        client,
        document_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Image"}],
    )
    assert response.status_code == 400, response.text


def test_a_kind_without_items_is_refused(client, document_notebook_id):
    response = _post_converter(
        client,
        document_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Text", "kinds": ["code"]}],
    )
    assert response.status_code == 400, response.text
    assert "code" in response.json()["detail"]


def test_an_absent_content_type_is_refused(client):
    notebook_id = create_document_notebook(client, "tools_text_only", ["a"])
    response = _post_converter(
        client, notebook_id, "CharacterReplacer", REPLACE, [{"columnName": "Image"}]
    )
    assert response.status_code == 400, response.text
    assert "Image" in response.json()["detail"]


def test_an_empty_document_scope_is_refused(client, document_notebook_id):
    response = _post_converter(
        client, document_notebook_id, "CharacterReplacer", REPLACE, []
    )
    assert response.status_code == 400, response.text


def test_a_target_is_refused_on_documents(client, document_notebook_id):
    response = _post_converter(
        client,
        document_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Text"}],
        target={"idx": 1},
    )
    assert response.status_code == 400, response.text


def test_an_unknown_converter_is_not_found(client, document_notebook_id):
    response = _post_converter(
        client, document_notebook_id, "Nope", {}, [{"columnName": "Text"}]
    )
    assert response.status_code == 404, response.text


def test_dataset_notebooks_still_accept_dataset_converters(client, dataset_notebook_id):
    response = _post_converter(
        client,
        dataset_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Species"}],
    )
    assert response.status_code == 201, response.text


def test_wordcloud_is_accepted_on_some_text_kinds(client, document_notebook_id):
    response = _post_explorer(
        client,
        document_notebook_id,
        "WordcloudExplorer",
        [{"columnName": "Text", "kinds": ["paragraph"]}],
        WORDS,
    )
    assert response.status_code == 201, response.text


def test_wordcloud_is_refused_on_document_images(client, document_notebook_id):
    response = _post_explorer(
        client,
        document_notebook_id,
        "WordcloudExplorer",
        [{"columnName": "Image"}],
        WORDS,
    )
    assert response.status_code == 400, response.text


def test_a_document_explorer_takes_one_content_type(client, document_notebook_id):
    response = _post_explorer(
        client,
        document_notebook_id,
        "WordcloudExplorer",
        [{"columnName": "Text"}, {"columnName": "Image"}],
        WORDS,
    )
    assert response.status_code == 400, response.text


def test_a_datasets_only_explorer_is_refused_on_documents(client, document_notebook_id):
    response = _post_explorer(
        client,
        document_notebook_id,
        "DescribeExplorer",
        [{"columnName": "Text"}],
        DESCRIBE,
    )
    assert response.status_code == 422, response.text


def test_dataset_notebooks_still_accept_dataset_explorers(client, dataset_notebook_id):
    response = _post_explorer(
        client,
        dataset_notebook_id,
        "DescribeExplorer",
        [{"columnName": "SepalLengthCm"}],
        DESCRIBE,
    )
    assert response.status_code == 201, response.text


def test_wordcloud_runs_on_the_selected_document_items(
    client: TestClient, document_notebook_id: int
):
    response = _post_explorer(
        client,
        document_notebook_id,
        "WordcloudExplorer",
        [{"columnName": "Text", "kinds": ["paragraph"]}],
        WORDS,
    )
    explorer_id = response.json()["id"]

    ExplorerJob(explorer_id=explorer_id).run()

    with client.app.container["session_factory"]() as db:
        explorer = db.get(Explorer, explorer_id)
        assert explorer.status == ExplorerStatus.FINISHED
        assert explorer.artifacts_path
    results = client.post(
        f"/api/v1/explorer/{explorer_id}/results/", json={"options": {}}
    )
    assert results.status_code == 200, results.text
    assert results.json()[0]["type"] == "image"


def test_picked_items_are_accepted(client, document_notebook_id):
    response = _post_converter(
        client,
        document_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Text", "positions": [1, 4]}],
    )
    assert response.status_code == 201, response.text


def test_a_picked_image_is_refused_as_text(client, document_notebook_id):
    response = _post_converter(
        client,
        document_notebook_id,
        "CharacterReplacer",
        REPLACE,
        [{"columnName": "Text", "positions": [2]}],
    )
    assert response.status_code == 400, response.text
    assert "positions 2" in response.json()["detail"]


class DocumentSampler(BaseConverter):
    """A row count changing converter that claims to run on documents."""

    SCHEMA = BaseConverterSchema
    CHANGES_ROW_COUNT = True
    metadata = {"data_kinds": [DOCUMENT], "allowed_types": [Text]}

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


class ItemDropper(DocumentConverter):
    """A document converter, allowed to change the number of items."""

    SCHEMA = BaseConverterSchema
    metadata = {"allowed_types": [Text]}

    def get_output_type(self, column_name=None):
        return Text(arrow_type=pa.string())

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x


@pytest.fixture(name="row_count_converters")
def fixture_row_count_converters(client: TestClient):
    registry = client.app.container["component_registry"]
    for component in (DocumentSampler, ItemDropper):
        registry.register_component(component)
    yield
    for component in (DocumentSampler, ItemDropper):
        registry.unregister_component(component)


def test_a_row_count_changing_converter_is_refused_on_documents(
    client, document_notebook_id, row_count_converters
):
    response = _post_converter(
        client, document_notebook_id, "DocumentSampler", {}, [{"columnName": "Text"}]
    )

    assert response.status_code == 400, response.text
    assert "DocumentConverter" in response.json()["detail"]


def test_a_document_converter_may_change_the_item_count(
    client, document_notebook_id, row_count_converters
):
    response = _post_converter(
        client, document_notebook_id, "ItemDropper", {}, [{"columnName": "Text"}]
    )

    assert response.status_code == 201, response.text


def test_a_document_converter_is_refused_on_datasets(
    client, dataset_notebook_id, row_count_converters
):
    response = _post_converter(
        client, dataset_notebook_id, "ItemDropper", {}, [{"columnName": "text"}]
    )

    assert response.status_code == 422, response.text
