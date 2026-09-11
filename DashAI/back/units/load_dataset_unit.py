"""Unit that loads a stored dataset into memory."""

import logging
from typing import TYPE_CHECKING

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    none_type,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Dataset, Notebook
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset

log = logging.getLogger(__name__)


class LoadDatasetSchema(BaseSchema):
    dataset_id: schema_field(
        none_type(int_field(gt=0)),
        placeholder=None,
        description=MultilingualString(
            en="Identifier of the stored dataset to load. Mutually exclusive "
            "with the notebook identifier.",
            es="Identificador del conjunto de datos almacenado a cargar. "
            "Excluyente con el identificador del cuaderno.",
            pt="Identificador do conjunto de dados armazenado a carregar. "
            "Mutuamente exclusivo com o identificador do caderno.",
            de="Kennung des zu ladenden gespeicherten Datensatzes. Schließt "
            "die Notebook-Kennung aus.",
            zh="要加载的已存储数据集的标识符。与笔记本标识符互斥。",
        ),
        alias=MultilingualString(
            en="Dataset",
            es="Conjunto de datos",
            pt="Conjunto de dados",
            de="Datensatz",
            zh="数据集",
        ),
    )  # type: ignore
    notebook_id: schema_field(
        none_type(int_field(gt=0)),
        placeholder=None,
        description=MultilingualString(
            en="Identifier of the notebook whose working copy of the dataset "
            "should be loaded. Mutually exclusive with the dataset identifier.",
            es="Identificador del cuaderno cuya copia de trabajo del conjunto "
            "de datos se debe cargar. Excluyente con el identificador del "
            "conjunto de datos.",
            pt="Identificador do caderno cuja cópia de trabalho do conjunto de "
            "dados deve ser carregada. Mutuamente exclusivo com o "
            "identificador do conjunto de dados.",
            de="Kennung des Notebooks, dessen Arbeitskopie des Datensatzes "
            "geladen werden soll. Schließt die Datensatz-Kennung aus.",
            zh="要加载其数据集工作副本的笔记本标识符。与数据集标识符互斥。",
        ),
        alias=MultilingualString(
            en="Notebook",
            es="Cuaderno",
            pt="Caderno",
            de="Notebook",
            zh="笔记本",
        ),
    )  # type: ignore


class LoadDatasetUnit(BaseUnit):
    """Load a dataset from disk into the execution context.

    Takes exactly one of two starting points and materialises the dataset each
    one points at, so downstream units receive a dataset instead of an
    identifier:

    * ``dataset_id``: the stored dataset itself, read from ``Dataset.file_path``.
    * ``notebook_id``: the notebook's own working copy, read from
      ``Notebook.file_path``. A notebook holds a private copy precisely so
      converters can rewrite it without touching the source dataset.

    Either way the unit publishes ``dataset_path``, which is where a later unit
    has to write the dataset back for the change to be visible.
    """

    SCHEMA = LoadDatasetSchema

    PROVIDES = ("dataset", "dataset_id", "dataset_path")

    def execute(self, ctx: ExecutionContext) -> None:
        from kink import di

        from DashAI.back.dataloaders.classes.dashai_dataset import load_dataset

        session_factory = di["session_factory"]

        dataset_id = self.config.get("dataset_id")
        notebook_id = self.config.get("notebook_id")

        if (dataset_id is None) == (notebook_id is None):
            raise JobError(
                "LoadDatasetUnit needs exactly one of dataset_id or notebook_id."
            )

        with session_factory() as db:
            if dataset_id is not None:
                dataset: Dataset = db.get(Dataset, dataset_id)
                if not dataset:
                    raise JobError(f"Dataset {dataset_id} does not exist in DB.")
                file_path = dataset.file_path
            else:
                notebook: Notebook = db.get(Notebook, notebook_id)
                if not notebook:
                    raise JobError(f"Notebook {notebook_id} does not exist in DB.")
                file_path = notebook.file_path
                # The notebook's copy still belongs to a source dataset, and
                # downstream error messages identify the work by that id.
                dataset_id = notebook.dataset_id

        dataset_path = f"{file_path}/dataset"

        try:
            loaded_dataset: "DashAIDataset" = load_dataset(dataset_path)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not load dataset from path {file_path}",
            ) from e

        if not loaded_dataset:
            raise JobError(f"Dataset with path {dataset_path} not found")

        ctx.put("dataset", loaded_dataset)
        ctx.put_ref("dataset_id", dataset_id)
        ctx.put_ref("dataset_path", dataset_path)
