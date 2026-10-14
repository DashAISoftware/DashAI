import pyarrow as pa

from DashAI.back.dataloaders.classes.dashai_data import DashAIData
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def test_dashai_dataset_is_dashai_data():
    dataset = DashAIDataset(pa.table({"a": [1, 2]}))

    assert isinstance(dataset, DashAIData)
    assert DashAIDataset.data_kind() == "dataset"
    assert dataset.data_kind() == "dataset"


def test_base_has_no_kind():
    assert DashAIData.data_kind() == ""
