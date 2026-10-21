import json
from types import SimpleNamespace

import pyarrow as pa
import pytest

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dataloaders.classes.document_items import items_with_details
from DashAI.back.exploration.explorers.text_statistics import (
    TextStatisticsExplorer,
    text_counts,
)
from DashAI.back.exploration.explorers.top_terms import TopTermsExplorer
from DashAI.back.types.value_types import Text
from tests.back.document_fixtures import build_document, text

INFO = SimpleNamespace(columns=[{"columnName": "Text"}], name=None, id=7)


def _document_input(items):
    return items_with_details(build_document(items), "Text")


def _dataset_input(values):
    table = pa.table({"Text": pa.array(values, type=pa.string())})
    return DashAIDataset(table, types={"Text": Text(arrow_type=pa.string())})


def _table_cells(figure):
    table = next(trace for trace in figure.data if trace.type == "table")
    return dict(zip(*table.cells.values, strict=True))


def test_text_counts():
    assert text_counts('  He said "Hi." Then left  ') == {
        "characters": 23,
        "words": 5,
        "sentences": 2,
    }
    assert text_counts("no end mark") == {
        "characters": 11,
        "words": 3,
        "sentences": 1,
    }
    assert text_counts("   ") == {"characters": 0, "words": 0, "sentences": 0}


def test_document_statistics_break_down_by_kind_and_page():
    dataset = _document_input(
        [
            text("Report", kind="title"),
            text("one two three.", page=1),
            text("four five", page=2),
            text("", page=2),
        ]
    )
    explorer = TextStatisticsExplorer()
    figure = explorer.launch_exploration(
        explorer.prepare_dataset(dataset, INFO.columns), INFO
    )
    cells = _table_cells(figure)
    assert cells["Items"] == 4
    assert cells["Words"] == 6
    assert cells["Empty items"] == 1
    boxes = [trace for trace in figure.data if trace.type == "box"]
    assert {box.name: list(box.y) for box in boxes} == {
        "title": [1],
        "paragraph": [3, 2, 0],
    }
    bars = next(trace for trace in figure.data if trace.type == "bar")
    assert dict(zip(bars.x, bars.y, strict=True)) == {1: 4, 2: 2}


def test_dataset_statistics_show_a_histogram():
    figure = TextStatisticsExplorer().launch_exploration(
        _dataset_input(["a b", None, "c"]), INFO
    )
    assert [trace.type for trace in figure.data] == ["table", "histogram"]
    assert _table_cells(figure)["Items"] == 3


def test_the_figure_round_trips_through_the_saved_file(tmp_path):
    explorer = TextStatisticsExplorer()
    figure = explorer.launch_exploration(_dataset_input(["a"]), INFO)
    path = explorer.save_notebook(None, INFO, tmp_path, figure)
    (artifact,) = explorer.get_results(path, {})
    assert artifact.type == "plotly"
    assert json.loads(artifact.payload)["data"][0]["type"] == "table"


def test_top_terms_count_and_skip_stop_words():
    explorer = TopTermsExplorer(top_n=3, min_words=1, max_words=1)
    ranked = explorer.rank(
        ["The data and the model", "data de los datos", "model data"]
    )
    assert ranked == [("data", 3.0), ("model", 2.0), ("datos", 1.0)]


def test_top_terms_find_pairs_and_keep_case_when_asked():
    explorer = TopTermsExplorer(
        top_n=1, min_words=2, max_words=2, stop_words="None", lowercase=False
    )
    assert explorer.rank(["New York New York", "new york"]) == [("New York", 2.0)]


def test_tfidf_favours_terms_of_few_items():
    explorer = TopTermsExplorer(top_n=1, max_words=1, score="TF-IDF")
    ranked = explorer.rank(["alpha beta", "alpha gamma", "alpha delta delta"])
    assert ranked[0][0] == "delta"


def test_no_terms_give_an_empty_chart():
    explorer = TopTermsExplorer()
    figure = explorer.launch_exploration(_dataset_input(["the", "", "de 12"]), INFO)
    assert list(figure.data[0].y) == []
    assert figure.layout.annotations


@pytest.mark.parametrize(
    ("params", "valid"),
    [
        ({"min_words": 1, "max_words": 3}, True),
        ({"min_words": 3, "max_words": 1}, False),
    ],
)
def test_term_length_must_be_ordered(params, valid):
    full = {
        "top_n": 20,
        "score": "Count",
        "stop_words": "None",
        "lowercase": True,
        **params,
    }
    assert TopTermsExplorer.validate_parameters(full) is valid


def test_text_explorers_run_on_datasets_and_documents():
    for explorer in (TextStatisticsExplorer, TopTermsExplorer):
        metadata = explorer.get_metadata()
        assert metadata["data_kinds"] == ["dataset", "document"]
        assert metadata["allowed_types"] == ["Text"]
        assert metadata["category"].en == "Text Analysis"
