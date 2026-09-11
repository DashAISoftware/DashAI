"""Unit that persists an exploration result under its notebook's folder."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Explorer, Notebook
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext

log = logging.getLogger(__name__)


class SaveExplorationSchema(BaseSchema):
    explorer_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the exploration being saved. It decides the "
            "destination folder and the file name, so a re-run overwrites its "
            "own artifact and never another exploration's.",
            es="Identificador de la exploración que se guarda. Determina la "
            "carpeta de destino y el nombre del archivo, de modo que volver a "
            "ejecutarla sobrescribe su propio artefacto y nunca el de otra.",
            pt="Identificador da exploração que está a ser guardada. Determina "
            "a pasta de destino e o nome do ficheiro, pelo que uma nova "
            "execução substitui o seu próprio artefacto e nunca o de outra.",
            de="Kennung der zu speichernden Exploration. Sie bestimmt "
            "Zielordner und Dateinamen, sodass ein erneuter Lauf nur das "
            "eigene Artefakt überschreibt und nie das einer anderen.",
            zh="要保存的探索的标识符。它决定目标文件夹和文件名，因此重新运行只会覆盖"
            "自身的产物，而不会覆盖其他探索的产物。",
        ),
        alias=MultilingualString(
            en="Exploration",
            es="Exploración",
            pt="Exploração",
            de="Exploration",
            zh="探索",
        ),
    )  # type: ignore


class SaveExplorationUnit(BaseUnit):
    """Write an exploration result to disk and publish where it landed.

    How the result is serialised is the explorer component's own business —
    a Plotly figure as JSON, a DataFrame as JSON, a word cloud as PNG — so the
    unit delegates to ``save_notebook`` and only owns the destination: the
    notebook's folder under ``NOTEBOOK_PATH``, keyed by the notebook id.

    The explorer arrives through the context rather than being rebuilt from a
    configuration of its own, so the object that saves is the object that ran.

    Declares only ``exploration_path``: the result itself is on disk, and the
    row that records the path belongs to the job.
    """

    SCHEMA = SaveExplorationSchema

    REQUIRES = ("exploration_result", "explorer")
    PROVIDES = ("exploration_path",)

    def execute(self, ctx: ExecutionContext) -> None:
        import os
        import pathlib

        from kink import di

        config = di["config"]
        session_factory = di["session_factory"]

        explorer_id = self.config["explorer_id"]
        explorer_instance = ctx.require("explorer")
        result = ctx.require("exploration_result")

        with session_factory() as db:
            explorer_info: Explorer = db.get(Explorer, explorer_id)
            if explorer_info is None:
                raise JobError(f"Explorer with id {explorer_id} not found.")

            notebook_info: Notebook = db.get(Notebook, explorer_info.notebook_id)
            if notebook_info is None:
                raise JobError(
                    f"Notebook with id {explorer_info.notebook_id} not found."
                )

            # Read while the row is still attached: the error message below is
            # built after the session is gone.
            exploration_type = explorer_info.exploration_type

            # save in the notebook folder
            save_path = pathlib.Path(
                os.path.join(
                    config["NOTEBOOK_PATH"],
                    (f"{notebook_info.id}"),
                )
            )
            if not save_path.exists():
                save_path.mkdir(parents=True)

            save_path = explorer_instance.save_notebook(
                notebook_info, explorer_info, save_path, result
            )

        if isinstance(save_path, str):
            save_path = pathlib.Path(save_path)
        if not isinstance(save_path, pathlib.Path):
            raise JobError(
                (
                    f"Error while saving the exploration"
                    f" {exploration_type}"
                    f", save path is not a pathlib.Path."
                )
            )

        ctx.put_ref("exploration_path", save_path.as_posix())
