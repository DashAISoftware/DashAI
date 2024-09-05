import os
import pathlib

import pandas as pd
from beartype.typing import Any, Dict

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.exploration.base_explorer import BaseExplorer


class DescribeExplorerSchema(BaseSchema):
    """Explorer1Schema is a schema for the Explorer1 class."""


class DescribeExplorer(BaseExplorer):
    SCHEMA = DescribeExplorerSchema

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs

    def launch_exploration(self, dataset: DashAIDataset) -> pd.DataFrame:
        _df = dataset.to_pandas()
        describe = _df.describe(include="all")
        return describe

    def save_exploration(
        self, explorer_info: Explorer, save_path: str, result: pd.DataFrame
    ) -> pathlib.Path:
        filename = f"{explorer_info.name}_{explorer_info.id}.json"
        path = pathlib.Path(os.path.join(save_path, filename))
        result.to_json(path)
        return path

    def get_results(self, exploration_path: str) -> Dict[str, Any]:
        path = pathlib.Path(exploration_path)
        result = pd.read_json(path).to_dict()
        return {"type": "tabular", "data": result}
