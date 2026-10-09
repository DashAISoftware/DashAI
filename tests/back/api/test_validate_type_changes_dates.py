import io
import json

from fastapi.testclient import TestClient

# The module scoped ``client`` fixture comes from tests/back/api/conftest.py.
# Defining a local one here would shadow it and break the autouse fixtures
# that depend on it.


def _post(client, csv_text, type_changes):
    return client.post(
        "/api/v1/dataset/validate_type_changes",
        data={
            "type_changes": json.dumps(type_changes),
            "params": json.dumps(
                {"dataloader_name": "CSVDataLoader", "separator": ","}
            ),
        },
        files={"file": ("series.csv", io.BytesIO(csv_text.encode()), "text/csv")},
    )


def test_endpoint_returns_the_detected_date_format(client: TestClient):
    csv_text = "when,sales\n01/02/2020,100\n05/02/2020,120\n13/02/2020,115\n"

    response = _post(
        client, csv_text, {"when": {"current_type": "Text", "new_type": "Date"}}
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["valid"] is True, payload["errors"]
    assert payload["resolved_dtypes"]["when"] == "%d/%m/%Y"


def test_endpoint_reports_an_unreadable_date_column(client: TestClient):
    csv_text = "when,sales\nQ1 2020,100\nQ2 2020,120\n"

    response = _post(
        client, csv_text, {"when": {"current_type": "Text", "new_type": "Date"}}
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["valid"] is False
    assert "when" in payload["errors"]
