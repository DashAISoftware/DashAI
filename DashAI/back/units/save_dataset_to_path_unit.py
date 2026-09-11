"""Unit that writes the dataset in the context to a destination of its own."""

import logging

from DashAI.back.core.schema_fields import BaseSchema, schema_field, string_field
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class SaveDatasetToPathSchema(BaseSchema):
    path: schema_field(
        string_field(),
        placeholder="",
        description=MultilingualString(
            en="Destination directory for the dataset. Unlike saving in place, "
            "this writes wherever it is told, so it can store a dataset that "
            "was loaded from somewhere else entirely.",
            es="Directorio de destino del conjunto de datos. A diferencia de "
            "guardar en su lugar, escribe donde se le indique, así que puede "
            "almacenar un conjunto de datos cargado desde otro origen.",
            pt="Diretório de destino do conjunto de dados. Ao contrário de "
            "guardar no lugar, escreve onde lhe for indicado, pelo que pode "
            "armazenar um conjunto de dados carregado de outra origem.",
            de="Zielverzeichnis für den Datensatz. Anders als beim Speichern am "
            "Ursprungsort schreibt diese Einheit dorthin, wo es ihr gesagt "
            "wird, und kann so einen anderswo geladenen Datensatz ablegen.",
            zh="数据集的目标目录。与原地保存不同，它会写入指定位置，因此可以存储"
            "从其他来源加载的数据集。",
        ),
        alias=MultilingualString(
            en="Destination path",
            es="Ruta de destino",
            pt="Caminho de destino",
            de="Zielpfad",
            zh="目标路径",
        ),
    )  # type: ignore


class SaveDatasetToPathUnit(BaseUnit):
    """Write the dataset to a destination given in the configuration.

    The sibling of ``SaveDatasetUnit``, and deliberately a separate unit rather
    than a flag on it. ``SaveDatasetUnit`` saves back to ``dataset_path`` — where
    the load came from — which is what makes editing a dataset in place safe. This
    one stores the dataset as something new, so it never reads ``dataset_path``:
    if it did, a flow that loads a working copy and registers the result as a
    fresh dataset would overwrite the copy it read.

    Declares no outputs — its result is on disk, not in the context.

    The error message keeps the original exception's text. A failure here is an
    infrastructure failure (out of space, permissions, a path the filesystem
    rejects), and only the message of the outermost error reaches the user: the
    job queue stores ``str(exc)``, never the ``__cause__`` chain. Swallowing it
    would drop the diagnosis exactly when it is needed.
    """

    SCHEMA = SaveDatasetToPathSchema

    REQUIRES = ("dataset",)
    PROVIDES = ()

    def execute(self, ctx: ExecutionContext) -> None:
        from DashAI.back.dataloaders.classes.dashai_dataset import save_dataset

        dataset = ctx.require("dataset")
        path = self.config["path"]

        try:
            save_dataset(dataset, path)
        except Exception as e:
            log.exception(e)
            raise JobError(f"Can not save dataset to path {path}: {e}") from e
