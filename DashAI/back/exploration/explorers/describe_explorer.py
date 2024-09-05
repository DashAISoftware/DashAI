import os

from DashAI.back.core.schema_fields import BaseSchema
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.dependencies.database.models import Explorer
from DashAI.back.exploration.base_explorer import BaseExplorer


class DescribeExplorerSchema(BaseSchema):
    """Explorer1Schema is a schema for the Explorer1 class."""

    params: dict


class DescribeExplorer(BaseExplorer):
    SCHEMA = DescribeExplorerSchema

    def __init__(self, **kwargs) -> None:
        self.kwargs = kwargs
        self.result = None

    def launch_exploration(self, dataset: DashAIDataset) -> DashAIDataset:
        _df = dataset.to_pandas()
        describe = _df.describe(include="all")
        self.result = describe
        return DashAIDataset.from_pandas(describe)

    def save_exploration(self, explorer_info: Explorer, save_path: str) -> str:
        filename = f"{explorer_info.name}_{explorer_info.id}.json"
        path = os.path.join(save_path, filename)
        self.result.to_json(path)
        return path
