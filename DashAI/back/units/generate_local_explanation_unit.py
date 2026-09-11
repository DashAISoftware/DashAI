"""Unit that explains individual instances and stores the result."""

import logging

from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    int_field,
    list_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.dependencies.database.models import Dataset
from DashAI.back.job.base_job import JobError
from DashAI.back.units.base_unit import BaseUnit
from DashAI.back.units.context import ExecutionContext
from DashAI.back.units.explanation_artifacts import dump_explanation

log = logging.getLogger(__name__)


def _columns_field(alias: MultilingualString, description: MultilingualString):
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=description,
        alias=alias,
    )


class GenerateLocalExplanationSchema(BaseSchema):
    explainer_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the local explanation being produced. It names "
            "the files on disk, so a re-run overwrites its own artifacts.",
            es="Identificador de la explicación local que se produce. Da nombre "
            "a los archivos en disco, de modo que volver a ejecutarla "
            "sobrescribe sus propios artefactos.",
            pt="Identificador da explicação local a ser produzida. Dá nome aos "
            "ficheiros em disco, pelo que uma nova execução substitui os seus "
            "próprios artefactos.",
            de="Kennung der erzeugten lokalen Erklärung. Sie benennt die "
            "Dateien auf der Festplatte, sodass ein erneuter Lauf nur die "
            "eigenen Artefakte überschreibt.",
            zh="所生成局部解释的标识符。它命名磁盘上的文件，因此重新运行只会覆盖自身产物。",
        ),
        alias=MultilingualString(
            en="Explanation",
            es="Explicación",
            pt="Explicação",
            de="Erklärung",
            zh="解释",
        ),
    )  # type: ignore
    instance_dataset_id: schema_field(
        int_field(gt=0),
        placeholder=1,
        description=MultilingualString(
            en="Identifier of the dataset the explained instances come from. "
            "It may differ from the one the model was trained on.",
            es="Identificador del conjunto de datos del que provienen las "
            "instancias explicadas. Puede diferir de aquel con el que se "
            "entrenó el modelo.",
            pt="Identificador do conjunto de dados de onde vêm as instâncias "
            "explicadas. Pode diferir daquele com que o modelo foi treinado.",
            de="Kennung des Datensatzes, aus dem die erklärten Instanzen "
            "stammen. Er kann sich von dem des Trainings unterscheiden.",
            zh="被解释实例所属数据集的标识符。它可能与模型训练所用的数据集不同。",
        ),
        alias=MultilingualString(
            en="Instance dataset",
            es="Conjunto de instancias",
            pt="Conjunto de instâncias",
            de="Instanzdatensatz",
            zh="实例数据集",
        ),
    )  # type: ignore
    scope: schema_field(
        dict,
        placeholder={"mode": "split", "split": "test", "percentage": 20},
        description=MultilingualString(
            en="Which instances to explain. A 'mode' of 'split' takes a share "
            "of one data split, 'rows' takes the row indexes the user marked, "
            "and 'manual' takes hand-typed values. Defaults to 'split'.",
            es="Qué instancias explicar. Un 'mode' de 'split' toma una "
            "proporción de una partición, 'rows' toma los índices de fila que "
            "marcó el usuario, y 'manual' toma valores ingresados a mano. Por "
            "defecto es 'split'.",
            pt="Que instâncias explicar. Um 'mode' de 'split' toma uma parte de "
            "uma partição, 'rows' toma os índices de linha que o utilizador "
            "marcou, e 'manual' toma valores introduzidos à mão. Por omissão é "
            "'split'.",
            de="Welche Instanzen erklärt werden. 'mode' 'split' nimmt einen "
            "Anteil einer Teilmenge, 'rows' die vom Benutzer markierten "
            "Zeilenindizes und 'manual' manuell eingegebene Werte. Standard "
            "ist 'split'.",
            zh="要解释哪些实例。'mode' 为 'split' 时取某个划分的一部分，"
            "'rows' 取用户标记的行索引，'manual' 取手工输入的值。默认为 'split'。",
        ),
        alias=MultilingualString(
            en="Scope", es="Alcance", pt="Âmbito", de="Umfang", zh="范围"
        ),
    )  # type: ignore
    fit_parameters: schema_field(
        dict,
        placeholder={},
        description=MultilingualString(
            en="Extra arguments handed to the explainer's fit step.",
            es="Argumentos adicionales entregados al paso de ajuste del explicador.",
            pt="Argumentos adicionais entregues ao passo de ajuste do explicador.",
            de="Zusätzliche Argumente für den Fit-Schritt des Erklärers.",
            zh="传递给解释器拟合步骤的额外参数。",
        ),
        alias=MultilingualString(
            en="Fit parameters",
            es="Parámetros de ajuste",
            pt="Parâmetros de ajuste",
            de="Fit-Parameter",
            zh="拟合参数",
        ),
    )  # type: ignore
    input_columns: _columns_field(
        alias=MultilingualString(
            en="Input columns",
            es="Columnas de entrada",
            pt="Colunas de entrada",
            de="Eingabespalten",
            zh="输入列",
        ),
        description=MultilingualString(
            en="Names of the columns used as model input.",
            es="Nombres de las columnas usadas como entrada del modelo.",
            pt="Nomes das colunas usadas como entrada do modelo.",
            de="Namen der als Modelleingabe verwendeten Spalten.",
            zh="用作模型输入的列名。",
        ),
    )  # type: ignore
    output_columns: _columns_field(
        alias=MultilingualString(
            en="Output columns",
            es="Columnas de salida",
            pt="Colunas de saída",
            de="Ausgabespalten",
            zh="输出列",
        ),
        description=MultilingualString(
            en="Names of the columns the model predicts.",
            es="Nombres de las columnas que el modelo predice.",
            pt="Nomes das colunas que o modelo prevê.",
            de="Namen der Spalten, die das Modell vorhersagt.",
            zh="模型需要预测的列名。",
        ),
    )  # type: ignore
    manual_input_data: schema_field(
        none_type(list),
        placeholder=None,
        description=MultilingualString(
            en="Rows to explain when the scope mode is 'manual'. Ignored otherwise.",
            es="Filas a explicar cuando el modo del alcance es 'manual'. Se "
            "ignora en otro caso.",
            pt="Linhas a explicar quando o modo do âmbito é 'manual'. Ignorado "
            "caso contrário.",
            de="Zu erklärende Zeilen, wenn der Modus 'manual' ist. Sonst ignoriert.",
            zh="范围模式为 'manual' 时要解释的行。其他情况下忽略。",
        ),
        alias=MultilingualString(
            en="Manual input",
            es="Entrada manual",
            pt="Entrada manual",
            de="Manuelle Eingabe",
            zh="手动输入",
        ),
    )  # type: ignore
    same_dataset: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Whether the instances come from the very dataset the model was "
            "trained on. When they do not, the run's row indexes mean nothing "
            "here and the split has to be recomputed.",
            es="Si las instancias provienen del mismo conjunto de datos con el "
            "que se entrenó el modelo. Si no, los índices de fila de la "
            "ejecución no significan nada acá y la partición se recalcula.",
            pt="Se as instâncias vêm do mesmo conjunto de dados com que o "
            "modelo foi treinado. Se não, os índices de linha da execução não "
            "significam nada aqui e a divisão tem de ser recalculada.",
            de="Ob die Instanzen aus genau dem Datensatz stammen, mit dem das "
            "Modell trainiert wurde. Andernfalls sind die Zeilenindizes des "
            "Laufs hier bedeutungslos und der Split wird neu berechnet.",
            zh="实例是否来自模型训练所用的同一数据集。若不是，则运行记录的行索引在此无意义，"
            "需要重新计算划分。",
        ),
        alias=MultilingualString(
            en="Same dataset",
            es="Mismo conjunto",
            pt="Mesmo conjunto",
            de="Gleicher Datensatz",
            zh="同一数据集",
        ),
    )  # type: ignore


class GenerateLocalExplanationUnit(BaseUnit):
    """Explain a selection of instances and pickle the result.

    Sibling of ``GenerateGlobalExplanationUnit``; see that class for why the
    two scopes are two units and not one with a branch.

    The three ways of choosing instances — a share of a split, the rows the
    user marked, or hand-typed values — stay one unit on purpose. They are
    three branches of a single decision with a single output; as separate
    nodes exactly one could ever run, which the contract cannot express.

    Row indexes are never taken on trust across datasets: when the instances
    come from a dataset other than the one the run was trained on, the run's
    indexes address rows that do not correspond, so the split is recomputed
    from the session's ratios instead. That derived state is resolved here,
    inside ``execute``, and never published.
    """

    SCHEMA = GenerateLocalExplanationSchema

    REQUIRES = ("explainer", "data_x", "data_y", "task", "split_indexes")
    PROVIDES = ("explanation_path", "plots_path", "input_dataset_path")
    RUNTIME_PARAMS = ("session_splits",)

    def _select_instances(self, prepared_instance, splits, instance, task):
        """Narrow the loaded dataset down to the instances to explain."""
        import json

        from datasets import DatasetDict

        from DashAI.back.dataloaders.classes.dashai_dataset import (
            prepare_for_model_session,
            select_columns,
            split_dataset,
        )

        scope = self.config["scope"] or {}
        input_columns = self.config["input_columns"]
        output_columns = self.config["output_columns"]

        # The data source is selected via scope["mode"]. It defaults to
        # "split" so explainers created before this field existed keep
        # their original split + percentage behavior.
        mode = scope.get("mode", "split")

        if mode == "manual":
            # Build the instances from values the user typed in by hand,
            # reusing the same conversion the manual prediction flow uses.
            # The rows (and any image files rewritten by the job endpoint)
            # travel in the job kwargs, not in scope.
            manual_input_data = self.config.get("manual_input_data") or []
            if not manual_input_data:
                raise JobError("No manual input data provided for the explanation")
            prepared_instance = task.process_manual_input(
                manual_input_data,
                f"{instance.file_path}/dataset",
            )
            # Manual input carries only the input columns (no target), so
            # keep just those instead of the standard input/output split.
            # select_columns returns a DashAIDataset (same shape the
            # split path produces), which is what the explainers expect.
            return prepared_instance.select_columns(input_columns)

        prepared_instance = task.prepare_for_task(
            prepared_instance,
            input_columns=input_columns,
            output_columns=output_columns,
        )

        if mode == "rows":
            # Explain a set of rows the user marked in the table.
            # Indexes are over the whole dataset (the split does not
            # apply in this mode).
            row_indexes = scope.get("row_indexes") or []
            valid_indexes = [
                i
                for i in row_indexes
                if isinstance(i, int) and 0 <= i < prepared_instance.num_rows
            ]
            if row_indexes and not valid_indexes:
                raise JobError("No valid row indexes provided for the explanation")
            if valid_indexes:
                prepared_instance = prepared_instance.select(valid_indexes)
        else:
            split = scope.get("split")
            if split not in ["train", "test", "val", "all"]:
                raise JobError(f"{split} is not a valid split")

            if split != "all":
                if not self.config["same_dataset"]:
                    if isinstance(splits, str):
                        splits = json.loads(splits)
                    (
                        prepared_dataset_dict,
                        splits,
                    ) = prepare_for_model_session(
                        dataset=prepared_instance,
                        splits=splits,
                        output_columns=output_columns,
                    )
                    split_key = "validation" if split == "val" else split
                    prepared_instance = prepared_dataset_dict[split_key]
                else:
                    prepared_instance = split_dataset(
                        prepared_instance,
                        train_indexes=splits["train_indexes"],
                        test_indexes=splits["test_indexes"],
                        val_indexes=splits["val_indexes"],
                    )
                    split_key = "validation" if split == "val" else split
                    prepared_instance = prepared_instance[split_key]

            n_rows = max(
                1,
                int(prepared_instance.num_rows * scope.get("percentage") / 100),
            )
            # When "shuffle" is set the percentage is taken as a random
            # sample of the split; otherwise it is the leading rows.
            if scope.get("shuffle"):
                prepared_instance = prepared_instance.shuffle(seed=42)
            prepared_instance = prepared_instance.select(range(n_rows))

        prepared_instance = DatasetDict({"train": prepared_instance})
        x, _ = select_columns(prepared_instance, input_columns, output_columns)
        return x

    def execute(self, ctx: ExecutionContext) -> None:
        import os

        from datasets import DatasetDict
        from kink import di

        from DashAI.back.core.artifacts import normalize_artifacts
        from DashAI.back.dataloaders.classes.dashai_dataset import (
            load_dataset,
            save_dataset,
        )

        config = di["config"]
        session_factory = di["session_factory"]

        explainer = ctx.require("explainer")
        task = ctx.require("task")
        dataset = (ctx.require("data_x"), ctx.require("data_y"))
        splits = ctx.require("split_indexes")

        explainer_id = self.config["explainer_id"]
        instance_id = self.config["instance_dataset_id"]

        # Fitting happens before the instances are even looked up, and is left
        # unwrapped on purpose: the explainer's own error is what the user gets.
        explainer.fit(dataset, **(self.config["fit_parameters"] or {}))

        if not self.config["same_dataset"]:
            splits = self.config["session_splits"]

        with session_factory() as db:
            instance: Dataset = db.get(Dataset, instance_id)
            if not instance:
                raise JobError(
                    f"Dataset {instance_id} to be explained does not exist in DB."
                )

            try:
                loaded_instance = load_dataset(f"{instance.file_path}/dataset")
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Can not load instance from path {instance.file_path}",
                ) from e

            try:
                x = self._select_instances(loaded_instance, splits, instance, task)

                # Persist the original selected rows (the model input for each
                # explained instance) as a DashAIDataset before the model's own
                # preprocessing runs, so the frontend can read them back with
                # the existing dataset endpoints.
                input_source = x["train"] if isinstance(x, DatasetDict) else x
                input_dataset_path = os.path.join(
                    config["EXPLANATIONS_PATH"],
                    f"local_explanation_input_{explainer_id}",
                )
                save_dataset(input_source, os.path.join(input_dataset_path, "dataset"))
                # The instances are handed over unprepared, the same way the
                # prediction job calls model.predict: the model applies its own
                # preprocessing. Explainers that need the model feature space
                # ask for it with prepare_model_input.

            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"""Can not prepare Dataset with {instance_id}
                        to generate the local explanation.""",
                ) from e

        try:
            explanation = explainer.explain_instance(x)
            plots = normalize_artifacts(
                explainer.plot(explanation), create_grouped=True
            )
        except Exception as e:
            log.exception(e)
            raise JobError(
                "Failed to generate the explanation",
            ) from e

        explanation_path, plots_path = dump_explanation(
            explanation, plots, "local", explainer_id
        )

        ctx.put_ref("explanation_path", explanation_path)
        ctx.put_ref("plots_path", plots_path)
        ctx.put_ref("input_dataset_path", input_dataset_path)
