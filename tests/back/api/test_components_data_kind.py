import pytest
from fastapi.testclient import TestClient

from DashAI.back.converters.base_converter import BaseConverter, BaseConverterSchema
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.exploration.base_explorer import BaseExplorer, BaseExplorerSchema


def _converter(name, data_kinds=None):
    metadata = {} if data_kinds is None else {"data_kinds": data_kinds}

    def get_output_type(self, column_name=None):
        return None

    def fit(self, x, y=None):
        return self

    def transform(self, x, y=None):
        return x

    return type(
        name,
        (BaseConverter,),
        {
            "SCHEMA": BaseConverterSchema,
            "metadata": metadata,
            "get_output_type": get_output_type,
            "fit": fit,
            "transform": transform,
        },
    )


def _explorer(name, data_kinds=None):
    metadata = {} if data_kinds is None else {"data_kinds": data_kinds}

    def launch_exploration(self, dataset, explorer_info):
        return None

    def save_notebook(self, notebook_info, explorer_info, save_path, result):
        return ""

    def get_results(self, exploration_path, options):
        return []

    return type(
        name,
        (BaseExplorer,),
        {
            "SCHEMA": BaseExplorerSchema,
            "metadata": metadata,
            "launch_exploration": launch_exploration,
            "save_notebook": save_notebook,
            "get_results": get_results,
        },
    )


class BaseThing:
    """A minimal component base that is not a data tool."""

    TYPE = "Thing"


class PlainThing(BaseThing):
    """A registered component without data kinds."""


@pytest.fixture(autouse=True, name="kind_registry")
def setup_kind_registry(client, monkeypatch: pytest.MonkeyPatch) -> ComponentRegistry:
    registry = ComponentRegistry(
        initial_components=[
            _converter("PlainConverter"),
            _converter("DocumentOnlyConverter", ["document"]),
            _converter("BothKindsConverter", ["dataset", "document"]),
            _explorer("PlainExplorer"),
            _explorer("BothKindsExplorer", ["dataset", "document"]),
            PlainThing,
        ]
    )
    monkeypatch.setitem(client.app.container._services, "component_registry", registry)
    return registry


def _names(response):
    assert response.status_code == 200, response.text
    return sorted(component["name"] for component in response.json())


def test_without_a_data_kind_every_component_is_returned(client: TestClient):
    assert _names(client.get("/api/v1/component/")) == [
        "BothKindsConverter",
        "BothKindsExplorer",
        "DocumentOnlyConverter",
        "PlainConverter",
        "PlainExplorer",
        "PlainThing",
    ]


def test_the_document_kind_keeps_only_document_tools(client: TestClient):
    response = client.get(
        "/api/v1/component/",
        params={"select_types": ["Converter", "Explorer"], "data_kind": "document"},
    )
    assert _names(response) == [
        "BothKindsConverter",
        "BothKindsExplorer",
        "DocumentOnlyConverter",
    ]


def test_the_dataset_kind_keeps_default_and_shared_tools(client: TestClient):
    response = client.get("/api/v1/component/", params={"data_kind": "dataset"})
    assert _names(response) == [
        "BothKindsConverter",
        "BothKindsExplorer",
        "PlainConverter",
        "PlainExplorer",
    ]


def test_an_unknown_data_kind_is_refused(client: TestClient):
    response = client.get("/api/v1/component/", params={"data_kind": "tabular"})
    assert response.status_code == 422, response.text
