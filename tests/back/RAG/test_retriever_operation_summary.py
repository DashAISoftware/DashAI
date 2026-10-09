"""Tests that composite retrievers expose a declarative operation summary."""

from fastapi.testclient import TestClient


def test_composite_operation_summaries(client: TestClient):
    registry = client.app.container["component_registry"]

    mmr = registry["MMRRerankerRetriever"]["metadata"]["operation_summary"]
    assert mmr == {
        "kind": "rerank",
        "fields": [
            {"param": "mmr_lambda", "label": "Lambda"},
            {"param": "top_k", "label": "Top K"},
        ],
    }

    cross = registry["SentenceTransformerCrossEncoderRetriever"]["metadata"][
        "operation_summary"
    ]
    assert cross == {
        "kind": "rerank",
        "fields": [{"param": "model_name", "label": ""}],
    }

    parallel = registry["ParallelRetriever"]["metadata"]["operation_summary"]
    assert parallel == {
        "kind": "fusion",
        "fields": [{"param": "merge_strategy", "label": ""}],
    }

    sequential = registry["SequentialRetriever"]["metadata"]["operation_summary"]
    assert sequential == {"kind": "fusion", "fields": []}
