"""End to end test for reports on a forecasting run.

A forecasting model refuses to return a value for dates inside its training
window, so the report job must not ask it to predict the train partition. It
should behave exactly like the prediction flow and cover only the partitions
that lie after the fit.
"""

import json
from pathlib import Path

import pandas as pd
import pytest
from fastapi.testclient import TestClient

from DashAI.back.core.enums.status import ReportStatus, RunStatus
from DashAI.back.dataloaders.classes.csv_dataloader import CSVDataLoader
from DashAI.back.dependencies.database.models import (
    Dataset,
    ModelSession,
    Report,
    Run,
)
from DashAI.back.dependencies.registry import ComponentRegistry
from DashAI.back.evaluation.forecasting_holdout import (
    ForecastingHoldoutEvaluationStrategy,
)
from DashAI.back.job.dataset_job import DatasetJob
from DashAI.back.job.model_job import ModelJob
from DashAI.back.job.report_job import ReportJob
from DashAI.back.models.forecasting.naive import NaiveForecaster
from DashAI.back.optimizers.optuna_optimizer import OptunaOptimizer
from DashAI.back.reports.forecasting.forecast_vs_actual import ForecastVsActual
from DashAI.back.splitters.temporal_holdout import TemporalHoldoutSplitter
from DashAI.back.tasks.forecasting_task import ForecastingTask


@pytest.fixture(scope="module", name="test_registry", autouse=True)
def setup_test_registry(client):
    container = client.app.container
    sentinel = object()
    services = container._services
    old = services.get("component_registry", sentinel)

    services["component_registry"] = ComponentRegistry(
        initial_components=[
            ForecastingTask,
            NaiveForecaster,
            CSVDataLoader,
            ModelJob,
            ReportJob,
            OptunaOptimizer,
            TemporalHoldoutSplitter,
            ForecastingHoldoutEvaluationStrategy,
            ForecastVsActual,
        ]
    )
    yield services["component_registry"]
    if old is sentinel:
        del services["component_registry"]
    else:
        services["component_registry"] = old


@pytest.fixture(scope="module", name="forecasting_dataset")
def create_forecasting_dataset(client: TestClient, test_path: Path):
    """Create a daily linear series dataset through the real DatasetJob."""
    dates = pd.date_range("2024-01-01", periods=60, freq="D").strftime("%Y-%m-%d")
    csv_path = Path(test_path) / "forecasting_report.csv"
    pd.DataFrame({"date": dates, "value": [float(i) for i in range(60)]}).to_csv(
        csv_path, index=False
    )

    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        entry = Dataset(name="forecasting_report", file_path="")
        db.add(entry)
        db.commit()
        db.refresh(entry)

        kwargs = {
            "dataset_id": entry.id,
            "url": "",
            "params": {
                "dataloader": "CSVDataLoader",
                "separator": ",",
                "name": entry.name,
                "schema": {
                    "date": {"type": "Date", "dtype": "%Y-%m-%d"},
                    "value": {"type": "Float", "dtype": "float64"},
                },
            },
            "file_path": csv_path,
        }
        DatasetJob(job_type="DatasetJob", kwargs=kwargs, db=db).run()
        db.refresh(entry)

        yield entry.id

        with session_factory() as cleanup:
            entry = cleanup.get(Dataset, entry.id)
            if entry:
                cleanup.delete(entry)
                cleanup.commit()


@pytest.fixture(scope="module", name="model_session_id")
def create_model_session(client: TestClient, forecasting_dataset: int):
    session_factory = client.app.container["session_factory"]
    with session_factory() as db:
        model_session = ModelSession(
            dataset_id=forecasting_dataset,
            name="ForecastingReportsSession",
            task_name="ForecastingTask",
            input_columns=["date"],
            output_columns=["value"],
            train_metrics=[],
            validation_metrics=[],
            test_metrics=[],
            evaluation_strategy="ForecastingHoldoutEvaluationStrategy",
            splits=json.dumps(
                {
                    "train": 0.6,
                    "test": 0.2,
                    "validation": 0.2,
                    "splitter_name": "TemporalHoldoutSplitter",
                    "splitType": "temporal",
                }
            ),
        )
        db.add(model_session)
        db.commit()
        db.refresh(model_session)

        yield model_session.id

        db.delete(model_session)
        db.commit()


@pytest.fixture(scope="module", name="trained_forecast_run_id")
def train_a_real_forecaster(client: TestClient, model_session_id: int, test_registry):
    response = client.post(
        "/api/v1/run/",
        json={
            "model_session_id": model_session_id,
            "model_name": "NaiveForecaster",
            "name": "ForecastingReportsRun",
            "parameters": {},
            "optimizer_name": "",
            "optimizer_parameters": {
                "n_trials": 1,
                "sampler": "TPESampler",
                "pruner": "None",
            },
            "goal_metric": "",
            "description": "Forecasting run under report",
            "plot_history_path": "path/to/history.png",
            "plot_slice_path": "path/to/slice.png",
            "plot_contour_path": "path/to/contour.png",
            "plot_importance_path": "path/to/importance.png",
        },
    )
    assert response.status_code == 201, response.text
    run_id = response.json()["id"]

    ModelJob(run_id=run_id).run()
    with client.app.container["session_factory"]() as db:
        assert db.get(Run, run_id).status == RunStatus.FINISHED

    yield run_id

    client.delete(f"/api/v1/run/{run_id}")


def test_a_forecasting_report_only_covers_forecastable_partitions(
    client: TestClient, trained_forecast_run_id: int
):
    """The train partition is a fit, not a forecast, so it must be skipped."""
    response = client.post(
        "/api/v1/report/",
        json={
            "run_id": trained_forecast_run_id,
            "report_name": "ForecastVsActual",
            "parameters": {},
        },
    )
    assert response.status_code == 201, response.text
    report_id = response.json()["id"]

    ReportJob(report_id=report_id).run()

    with client.app.container["session_factory"]() as db:
        assert db.get(Report, report_id).status == ReportStatus.FINISHED

    artifacts = client.get(f"/api/v1/report/{report_id}/artifacts").json()
    assert len(artifacts) == 1
    assert artifacts[0]["type"] == "grouped"

    titles = [group["title"] for group in artifacts[0]["groups"]]
    assert titles == ["Test", "Validation"]

    for group in artifacts[0]["groups"]:
        leaf = group["artifacts"][0]
        assert leaf["type"] == "plotly"
        figure = json.loads(leaf["payload"])
        assert [trace["name"] for trace in figure["data"]] == [
            "Actual",
            "Forecast",
        ]

    client.delete(f"/api/v1/report/{report_id}")
