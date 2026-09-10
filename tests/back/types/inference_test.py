import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from DashAI.back.app import create_app
from DashAI.back.types.inf.type_inference import infer_types

DATA_DIR = Path(__file__).parent


def _infer(client, file_path: Path, mime: str, params: dict):
    with file_path.open("rb") as f:
        files = {"file": (file_path.name, f, mime)}
        data = {"params": json.dumps(params)}
        resp = client.post(
            "/api/v1/dataset/preview_with_types",
            data=data,
            files=files,
        )
    assert resp.status_code == 200, resp.text
    payload = resp.json()
    return payload.get("inferred_types", {})


@pytest.fixture
def client(tmp_path: Path):
    app = create_app(local_path=tmp_path, logging_level="ERROR", enable_seeding=False)
    with TestClient(app) as c:
        yield c


def test_inference_consistency(client: TestClient):
    csv_path = DATA_DIR / "iris.csv"
    json_path = DATA_DIR / "iris.json"
    xslx_path = DATA_DIR / "iris.xlsx"

    for p in [csv_path, json_path, xslx_path]:
        if not p.exists():
            pytest.skip(f"File {p.name} not found in {DATA_DIR}, skipping test.")

    inferred_csv = _infer(
        client,
        csv_path,
        "text/csv",
        {
            "separator": ",",
            "methods": ["DashAIPtype"],
            "dataloader_name": "CSVDataLoader",
        },
    )
    inferred_json = _infer(
        client,
        json_path,
        "application/json",
        {
            "data_key": "data",
            "methods": ["DashAIPtype"],
            "dataloader_name": "JSONDataLoader",
        },
    )
    # TEST API PROBLEM DOESNT LET USE XLSX SAME AS ABOVE. DOESN'T HAPPEN IN REAL USE.
    df_xslx = pd.read_excel(xslx_path)
    inferred_xslx = infer_types(df_xslx, method="DashAIPtype")

    expected_float = ["SepalLengthCm", "SepalWidthCm", "PetalLengthCm", "PetalWidthCm"]
    expected_float_json = ["feature_0", "feature_1", "feature_2", "feature_3"]
    expected_categorical = ["Species"]
    expected_categorical_json = ["class"]

    # This is just because i'm too lazy to change the test data
    for col in expected_float:
        assert inferred_csv[col].get("type") == "Float"
        assert inferred_xslx[col].get("type") == "Float"

    for col in expected_float_json:
        assert inferred_json[col].get("type") == "Float"

    for col in expected_categorical:
        assert inferred_csv[col].get("type") == "Categorical"
        assert inferred_xslx[col].get("type") == "Categorical"

    for col in expected_categorical_json:
        assert inferred_json[col].get("type") == "Categorical"


def test_infer_date_and_time():
    date_df = pd.DataFrame(
        {
            "fecha": ["2024-01-01", "2024-02-29", "2025-12-31"],
            "hora": ["08:30:00", "14:05:10", "23:59:59"],
            "float_col": [1.1, 2.2, 3.3],
            "text_col": ["a", "b", "c"],
        }
    )

    inferred = infer_types(date_df, method="DashAIPtype")

    # Dates are a real type now, carrying the strptime format read off the
    # values. Times are not: no format can be inferred for them, so they stay
    # Text until something needs them.
    assert inferred["fecha"]["type"] == "Date"
    assert inferred["fecha"]["dtype"] == "%Y-%m-%d"
    assert inferred["hora"]["type"] == "Text"
    assert "type" in inferred["float_col"]
    assert "type" in inferred["text_col"]


def test_infer_float_comma_float():
    numeric_df = pd.DataFrame(
        {
            "float_comma": ["1,23", "4,56", "7,89"],
            "float_dot": ["1.23", "4.56", "7.89"],
            "int_col": ["1", "2", "3"],
        }
    )

    inferred = infer_types(numeric_df, method="DashAIPtype")

    assert inferred["float_comma"]["type"] == "Float"
    assert inferred["float_dot"]["type"] == "Float"
    assert inferred["int_col"]["type"] == "Integer"


def test_dummy_different_from_dashaiptype():
    sample_df = pd.DataFrame(
        {
            "few_int": [1, 2, 3, 4, 5, 6],
            "float_comma": ["1,23", "2,34", "3,45", "4,56", "5,67", "6,78"],
            "float_dot": ["1.2", "3.4", "5.6", "7.8", "9.0", "10.1"],
        }
    )

    inferred_ptype = infer_types(sample_df, method="DashAIPtype")
    inferred_dummy = infer_types(sample_df, method="Dummy")

    assert inferred_ptype["few_int"]["type"] != inferred_dummy["few_int"]["type"]

    assert (
        inferred_ptype["float_comma"]["type"] != inferred_dummy["float_comma"]["type"]
    )

    assert inferred_ptype["float_dot"]["type"] in {"Float", "String", "Categorical"}
    assert inferred_dummy["float_dot"]["type"] in {"Float", "String", "Categorical"}


def test_dashaptype_infers_one_hot_for_string_categorical():
    """String categorical columns get encoder='one_hot'."""
    import pandas as pd

    from DashAI.back.types.inf.inference_methods import DashAIPtype

    data = pd.DataFrame({"color": ["red", "blue", "red", "green", "blue"]})
    result = DashAIPtype().infer_types(data)

    assert result["color"]["type"] == "Categorical"
    assert result["color"]["encoder"] == "one_hot"


def test_dashaptype_infers_label_for_int_categorical():
    """Integer categorical columns get encoder='label'."""
    import pandas as pd

    from DashAI.back.types.inf.inference_methods import DashAIPtype

    # Binary integer labels (0/1) over 100 rows
    # ptype reliably classifies as categorical
    data = pd.DataFrame({"grade": [0, 1] * 50})
    result = DashAIPtype().infer_types(data)

    assert result["grade"]["type"] == "Categorical", (
        f"Expected 'grade' to be Categorical, got {result['grade']['type']}"
    )
    assert result["grade"]["encoder"] == "label"


def test_dummy_infers_one_hot_for_string_categorical():
    """DummyCategoricalInference: string categoricals get one_hot."""
    import pandas as pd

    from DashAI.back.types.inf.inference_methods import DummyCategoricalInference

    data = pd.DataFrame({"animal": ["cat", "dog", "cat", "fish", "dog"]})
    result = DummyCategoricalInference().infer_types(data)

    assert result["animal"]["type"] == "Categorical"
    assert result["animal"]["encoder"] == "one_hot"


def test_dummy_infers_label_for_int_categorical():
    """DummyCategoricalInference: int categoricals get label."""
    import pandas as pd

    from DashAI.back.types.inf.inference_methods import DummyCategoricalInference

    data = pd.DataFrame({"code": [0, 1, 2, 0, 1, 2, 0, 1, 2]})
    result = DummyCategoricalInference().infer_types(data)

    assert result["code"]["type"] == "Categorical"
    assert result["code"]["encoder"] == "label"
