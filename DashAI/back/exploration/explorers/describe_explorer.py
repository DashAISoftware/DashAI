import os
import pathlib

import numpy as np
import pandas as pd
from beartype.typing import Any, Dict

from DashAI.back.core.schema_fields import (
    enum_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dependencies.database.models import Exploration, Explorer
from DashAI.back.exploration.base_explorer import BaseExplorer, BaseExplorerSchema


class DescribeExplorerSchema(BaseExplorerSchema):
    """
    DescribeExplorerSchema is an explorer that returns the descriptive \
    statistics of a dataset.
    """

    percentiles: schema_field(
        none_type(string_field()),
        None,
        (
            "The percentiles to include in the exploration. "
            "Must be a list of integers between 0 and 100.\n"
            "Defaults to: '25, 50, 75'"
        ),
    )  # type: ignore
    include: schema_field(
        enum_field(["all", "number", "object", "category", "datetime"]),
        "number",
        ("The data types to include in the exploration.\n" "Defaults to: 'number'"),
    )  # type: ignore
    exclude: schema_field(
        none_type(enum_field(["object", "number", "category", "datetime"])),
        None,
        ("The data types to exclude in the exploration." "Defaults to: None"),
    )  # type: ignore


class DescribeExplorer(BaseExplorer):
    SCHEMA = DescribeExplorerSchema

    metadata: Dict[str, Any] = {
        "allowed_dtypes": ["*"],
        "restricted_dtypes": [],
        "input_cardinality": {"min": 1},
    }

    def __init__(self, **kwargs) -> None:
        parameters = kwargs

        # transform percentiles to list of floats for describe (e.g., [0.25, 0.5, 0.75])
        if parameters.get("percentiles"):
            percentiles = parameters["percentiles"].split(",")
            percentiles = [percentile.strip() for percentile in percentiles]

            if percentiles == [""]:
                percentiles = ["25", "50", "75"]
            percentiles = [float(percentile) / 100 for percentile in percentiles]
            parameters["percentiles"] = percentiles

        self.kwargs = kwargs
        self.percentiles = parameters["percentiles"]
        self.include = parameters["include"]
        self.exclude = parameters["exclude"]

    @classmethod
    def validate_parameters(cls, params: Dict[str, Any]) -> bool:
        # Validate schema
        cls.SCHEMA.model_validate(params)

        # Validate percentiles (must be int between 0 and 100)
        if params.get("percentiles"):
            percentiles = params["percentiles"].split(",")
            for percentile in percentiles:
                try:
                    int_percentile = int(percentile)
                    if not 0 <= int_percentile <= 100:
                        return False
                except ValueError:
                    return False
        return True

    def launch_exploration(self, dataset: DashAIDataset) -> pd.DataFrame:
        _df = dataset.to_pandas()

        percentiles = self.percentiles
        include = self.include
        exclude = self.exclude

        if include == "number":
            include = None
        elif include == "all":
            pass
        else:
            include = list(include)
        exclude = None if exclude is None else list(exclude)

        result = _df.describe(percentiles=percentiles, include=include, exclude=exclude)
        return result

    def save_exploration(
        self,
        exploration_info: Exploration,
        explorer_info: Explorer,
        save_path: str,
        result: pd.DataFrame,
    ) -> str:
        if explorer_info.name is None or explorer_info.name == "":
            filename = f"{exploration_info.id}_{explorer_info.id}.json"
        else:
            filename = f"{explorer_info.name}_{explorer_info.id}.json"
        path = pathlib.Path(os.path.join(save_path, filename))

        result.to_json(path)
        return path.as_posix()

    def get_results(
        self, exploration_path: str, options: Dict[str, Any]
    ) -> Dict[str, Any]:
        resultType = "tabular"
        orientation = options.get("orientation", "dict")
        config = {"orient": orientation}

        path = pathlib.Path(exploration_path)
        result = (
            pd.read_json(path).replace({np.nan: None}).T.to_dict(orient=orientation)
        )
        return {"type": resultType, "data": result, "config": config}
