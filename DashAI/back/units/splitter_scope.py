"""Shared body of the two units that prepare a dataset and partition it.

``PrepareAndSplitUnit`` and ``PrepareAndFoldUnit`` do the same four things --
resolve the task, prepare the dataset for it, separate features from targets,
and hand the pair to a splitter -- and differ only in which family of splitters
they offer and in the shape of what comes back. Keeping the body here is what
stops the two from drifting into two answers for the same dataset.

When the session ran a preprocessing sequence there is a fifth thing, done
after the split: every entry the splitter produced is transformed with the
``SessionPreprocessor`` that ``PreprocessingJob`` fitted for it, so nothing
downstream ever sees a raw column the model was not meant to read.

Named ``SplitterScopeMixin`` rather than ``BaseSomething`` on purpose: the
registry derives a component's type by walking its ``__mro__`` for a class whose
name contains "Base" and that declares ``TYPE``, and demands exactly one. A
shared parent called ``Base*`` would be a second candidate and would break the
registration of every unit that inherited it.
"""

import logging
from typing import TYPE_CHECKING, Any, Dict, List, NamedTuple, Optional, Tuple

from DashAI.back.core.schema_fields import (
    component_field,
    list_field,
    none_type,
    schema_field,
    string_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.job.base_job import JobError

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
    from DashAI.back.splitters.base_splitter import BaseSplitter
    from DashAI.back.tasks.base_task import BaseTask

log = logging.getLogger(__name__)


def task_name_field():
    return schema_field(
        string_field(),
        placeholder="TabularClassificationTask",
        description=MultilingualString(
            en="Name of the task the dataset is prepared for.",
            es="Nombre de la tarea para la que se prepara el conjunto de datos.",
            pt="Nome da tarefa para a qual o conjunto de dados é preparado.",
            de="Name der Aufgabe, für die der Datensatz vorbereitet wird.",
            zh="数据集所准备的任务名称。",
        ),
        alias=MultilingualString(
            en="Task", es="Tarea", pt="Tarefa", de="Aufgabe", zh="任务"
        ),
    )


def input_columns_field():
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns used as model input.",
            es="Nombres de las columnas usadas como entrada del modelo.",
            pt="Nomes das colunas usadas como entrada do modelo.",
            de="Namen der als Modelleingabe verwendeten Spalten.",
            zh="用作模型输入的列名。",
        ),
        alias=MultilingualString(
            en="Input columns",
            es="Columnas de entrada",
            pt="Colunas de entrada",
            de="Eingabespalten",
            zh="输入列",
        ),
    )


def output_columns_field():
    return schema_field(
        list_field(string_field(), min_items=1),
        placeholder=[],
        description=MultilingualString(
            en="Names of the columns the model has to predict.",
            es="Nombres de las columnas que el modelo debe predecir.",
            pt="Nomes das colunas que o modelo deve prever.",
            de="Namen der Spalten, die das Modell vorhersagen soll.",
            zh="模型需要预测的列名。",
        ),
        alias=MultilingualString(
            en="Output columns",
            es="Columnas de salida",
            pt="Colunas de saída",
            de="Ausgabespalten",
            zh="输出列",
        ),
    )


def input_column_refs_field():
    """The columns the model reads, as references a session stores.

    Optional, and only meaningful next to ``preprocessing_artifacts_path``: a
    raw ref names a column of the dataset, a group ref names whatever a
    converter step produces, and the latter only resolves against the fit
    the job persisted at that path. Without the pair, ``input_columns`` is
    what the model reads.
    """
    return schema_field(
        none_type(list),
        placeholder=None,
        description=MultilingualString(
            en="Column references the model reads when the session ran a "
            "preprocessing sequence: {'kind': 'raw', 'name': ...} for a "
            "column of the dataset, {'kind': 'group', 'step': n} for what "
            "converter step n produces. Set together with the artifacts path, "
            "or not at all.",
            es="Referencias a las columnas que lee el modelo cuando la sesión "
            "ejecutó una secuencia de preprocesamiento: {'kind': 'raw', "
            "'name': ...} para una columna del conjunto de datos, {'kind': "
            "'group', 'step': n} para lo que produce el paso n. Se indica "
            "junto con la ruta de artefactos, o no se indica.",
            pt="Referências às colunas que o modelo lê quando a sessão executou "
            "uma sequência de pré-processamento: {'kind': 'raw', 'name': ...} "
            "para uma coluna do conjunto de dados, {'kind': 'group', 'step': "
            "n} para o que o passo n produz. Indica-se junto com o caminho "
            "dos artefatos, ou não se indica.",
            de="Spaltenreferenzen, die das Modell liest, wenn die Sitzung eine "
            "Vorverarbeitungssequenz ausgeführt hat: {'kind': 'raw', 'name': "
            "...} für eine Spalte des Datensatzes, {'kind': 'group', 'step': "
            "n} für das, was Schritt n erzeugt. Zusammen mit dem Artefaktpfad "
            "angeben, oder gar nicht.",
            zh="会话运行了预处理序列时模型读取的列引用：{'kind': 'raw', "
            "'name': ...} 表示数据集的列，{'kind': 'group', 'step': n} 表示"
            "第 n 步转换器产生的列。与工件路径一起设置，或都不设置。",
        ),
        alias=MultilingualString(
            en="Input column references",
            es="Referencias de columnas de entrada",
            pt="Referências de colunas de entrada",
            de="Eingabespaltenreferenzen",
            zh="输入列引用",
        ),
    )


def preprocessing_artifacts_path_field():
    """Where the session's fitted preprocessors live.

    Optional. ``PreprocessingJob`` writes one fitted ``SessionPreprocessor``
    per entry the splitter produces, ``fold_{i}.pkl`` and ``final.pkl``, and
    the unit loads the matching one for each entry it publishes.
    """
    return schema_field(
        none_type(string_field()),
        placeholder=None,
        description=MultilingualString(
            en="Directory holding the preprocessing fitted for this session, "
            "one artifact per split entry. Set together with the input column "
            "references, or not at all.",
            es="Directorio con el preprocesamiento ajustado para esta sesión, "
            "un artefacto por entrada de la partición. Se indica junto con "
            "las referencias de columnas de entrada, o no se indica.",
            pt="Diretório com o pré-processamento ajustado para esta sessão, "
            "um artefato por entrada da partição. Indica-se junto com as "
            "referências de colunas de entrada, ou não se indica.",
            de="Verzeichnis mit der für diese Sitzung angepassten "
            "Vorverarbeitung, ein Artefakt pro Aufteilungseintrag. Zusammen "
            "mit den Eingabespaltenreferenzen angeben, oder gar nicht.",
            zh="存放为此会话拟合的预处理的目录，每个划分条目一个工件。"
            "与输入列引用一起设置，或都不设置。",
        ),
        alias=MultilingualString(
            en="Fitted preprocessing",
            es="Preprocesamiento ajustado",
            pt="Pré-processamento ajustado",
            de="Angepasste Vorverarbeitung",
            zh="已拟合的预处理",
        ),
    )


def _splitter_field(parent: str, placeholder: Dict[str, Any]):
    """A splitter chosen from one family, with its own configuration.

    Parameters
    ----------
    parent : str
        Class name every offered splitter has in its ``__mro__``. The two
        families are told apart here rather than by a flag, because the front
        resolves the choices with ``component_parent``, which matches any
        ancestor by name: ``PartitionSplitter`` offers the two holdout
        splitters and ``FoldSplitter`` the eight fold ones, with no renaming
        and no change to the registry.
    placeholder : dict
        The ``{"component": …, "params": {…}}`` value the form starts on.
    """
    return schema_field(
        component_field(parent=parent),
        placeholder=placeholder,
        description=MultilingualString(
            en="Splitter that decides how the dataset is partitioned, along "
            "with its own configuration.",
            es="Particionador que decide cómo se divide el conjunto de datos, "
            "junto con su propia configuración.",
            pt="Divisor que decide como o conjunto de dados é particionado, "
            "junto com a sua própria configuração.",
            de="Splitter, der über die Aufteilung des Datensatzes entscheidet, "
            "samt seiner eigenen Konfiguration.",
            zh="决定数据集如何划分的划分器及其自身配置。",
        ),
        alias=MultilingualString(
            en="Splitter",
            es="Particionador",
            pt="Divisor",
            de="Splitter",
            zh="划分器",
        ),
    )


def partition_splitter_field():
    """The field of the unit that splits once, offering the holdout family."""
    return _splitter_field(
        parent="PartitionSplitter",
        placeholder={
            "component": "HoldoutSplitter",
            "params": {
                "train": 0.6,
                "test": 0.2,
                "validation": 0.2,
                "stratify": False,
                "shuffle": True,
                "random_state": 42,
            },
        },
    )


def fold_splitter_field():
    """The field of the unit that splits into folds, offering the fold family."""
    return _splitter_field(
        parent="FoldSplitter",
        placeholder={
            "component": "KFoldSplitter",
            "params": {
                "n_splits": 5,
                "test_size": 0.1,
                "shuffle": True,
                "random_state": 42,
            },
        },
    )


class PersistedPreprocessing(NamedTuple):
    """A session's fitted preprocessing, as the two prepare units receive it.

    Built from the two optional fields by ``_persisted_preprocessing``. The
    units never read it from the context: it describes what a job already
    did for the session, not what an upstream unit produced.
    """

    #: Directory where ``PreprocessingJob`` persisted one fitted
    #: ``SessionPreprocessor`` per entry the splitter produces, as
    #: ``fold_{i}.pkl`` and ``final.pkl``.
    artifacts_path: str
    #: The parsed column references the model reads. A raw one names a column
    #: of the dataset; a group one names the output of a converter step, which
    #: only exists once that step has run.
    input_refs: List[Any]

    @property
    def raw_input_names(self) -> List[str]:
        """The refs that name a column present before any converter runs."""
        return [ref.name for ref in self.input_refs if ref.kind == "raw"]


class SplitterScopeMixin:
    """Prepare a dataset for a task and hand it to a splitter.

    Every method here takes and returns plain values and never touches the
    execution context. A ``ctx.put`` hidden in a shared helper is invisible to
    the audit that parses each unit's own source, so a broken ``PROVIDES``
    would pass it.
    """

    #: Declared here so both the memoizing helpers and a reader can see what
    #: state an instance carries; each unit sets them in its own ``__init__``,
    #: because ``BaseUnit.__init__`` comes first in the MRO and does not chain.
    _task = None
    _splitter_class = None

    @property
    def splitter_name(self) -> str:
        return self.config["splitter"]["component"]

    @property
    def splitter_params(self) -> Dict[str, Any]:
        return self.config["splitter"]["params"]

    def _resolve_task(self) -> "BaseTask":
        """Instantiate the task, memoized on this unit.

        On the instance rather than in the context: a context can hold two of
        these units, and a context-global cache would silently give the second
        one the first one's task.
        """
        if self._task is not None:
            return self._task

        from kink import di

        task_name: str = self.config["task_name"]
        try:
            self._task = di["component_registry"][task_name]["class"]()
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Unable to find Task with name {task_name} in registry",
            ) from e
        return self._task

    def _resolve_splitter(self) -> "BaseSplitter":
        """Build the configured splitter.

        ``BaseSplitter.__init__`` takes a single ``splits_data`` mapping rather
        than keyword arguments, so this is the one component field in the units
        that is not expanded with ``**params``. The shape is the splitter's own
        schema either way; only how it is handed over differs.
        """
        from kink import di

        splitter_name = self.splitter_name
        if self._splitter_class is None:
            try:
                self._splitter_class = di["component_registry"][splitter_name]["class"]
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Unable to find Splitter with name {splitter_name} in registry.",
                ) from e

        try:
            return self._splitter_class(splits_data=dict(self.splitter_params))
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error instantiating splitter {splitter_name}, {e}",
            ) from e

    @staticmethod
    def _persisted_preprocessing(
        artifacts_path: Optional[str], input_column_refs: Optional[List[dict]]
    ) -> Optional[PersistedPreprocessing]:
        """Pair the two optional fields, or None when the session has no steps.

        They come together or not at all. A ref that names a converter's
        output group only resolves against the fit that produced it, and a
        fitted sequence with no refs leaves the model with no columns to read.
        So one without the other is a wiring mistake, and it is reported as
        one rather than read as "not applicable".
        """
        if artifacts_path is None and input_column_refs is None:
            return None
        if artifacts_path is None or input_column_refs is None:
            raise JobError(
                "preprocessing_artifacts_path and input_column_refs come "
                "together: a session with preprocessing steps supplies both.",
            )

        from DashAI.back.preprocessing.column_ref import parse_column_refs

        try:
            input_refs = parse_column_refs(input_column_refs)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not parse input column refs {input_column_refs}: {e}",
            ) from e
        return PersistedPreprocessing(
            artifacts_path=artifacts_path, input_refs=input_refs
        )

    def _prepare(
        self,
        dataset: "DashAIDataset",
        dataset_id: Any,
        preprocessing: Optional[PersistedPreprocessing] = None,
    ) -> Tuple["BaseTask", int, "DashAIDataset", "DashAIDataset"]:
        """Validate the dataset against the task and separate x from y.

        Parameters
        ----------
        dataset : DashAIDataset
            The loaded dataset.
        dataset_id : Any
            Only decorates the error messages.
        preprocessing : PersistedPreprocessing, optional
            The session's fitted preprocessing, when it has one. The
            converters run per entry after the split, so at this point only
            the raw refs name columns that exist: those are what the task
            validates, and ``x`` keeps every column of the prepared dataset
            rather than the inputs, because a converter's scope may name a
            column that is not itself a final input. ``y`` is narrowed either
            way, since an output ref is always raw.

        Returns
        -------
        tuple
            The task, the number of labels, and the input and output datasets,
            in that order. Nothing here is written to the context: the unit
            that called this decides what it promises.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import select_columns

        task = self._resolve_task()
        task_name: str = self.config["task_name"]
        input_columns: List[str] = self.config["input_columns"]
        output_columns: List[str] = self.config["output_columns"]
        if preprocessing is not None:
            input_columns = preprocessing.raw_input_names

        try:
            prepared_dataset = task.prepare_for_task(
                dataset=dataset,
                input_columns=input_columns,
                output_columns=output_columns,
            )
            n_labels = task.num_labels(prepared_dataset, output_columns[0])
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Can not prepare Dataset {dataset_id} for Task {task_name}",
            ) from e

        try:
            # Read from the prepared dataset rather than the loaded one: a task
            # may reorder the rows, and forecasting does, sorting them by date
            # so a temporal splitter carves real periods of time. Selecting
            # from the loaded dataset would drop that work on the floor.
            if preprocessing is not None:
                x = prepared_dataset
                y = prepared_dataset.select_columns(output_columns)
            else:
                x, y = select_columns(prepared_dataset, input_columns, output_columns)
        except Exception as e:
            log.exception(e)
            raise JobError(
                f"Error selecting input and output columns from dataset {dataset_id}",
            ) from e

        return task, n_labels, x, y

    @staticmethod
    def _apply_preprocessing(
        entries: List[Dict[str, "DashAIDataset"]],
        names: List[str],
        preprocessing: PersistedPreprocessing,
        output_columns: List[str],
    ) -> Tuple[List[Dict[str, "DashAIDataset"]], List[Dict[str, "DashAIDataset"]]]:
        """Transform each entry the splitter produced with the fit made for it.

        ``PreprocessingJob`` fitted one ``SessionPreprocessor`` per entry, on
        that entry's own training partition, and persisted it under
        ``artifacts_path`` as ``{name}.pkl``: ``fold_{i}`` for each fold and
        ``final`` for the trailing entry, which for a holdout split is the
        only one. Loading the matching one here is what keeps a fold from
        seeing statistics fitted on the rows it is scored on.

        Pure on purpose: it takes the entries and returns new ones without
        touching the context, so the audit that parses each unit's own source
        still sees every key the unit publishes.

        Parameters
        ----------
        entries : list of dict
            What the splitter returned for the input side, one
            ``{partition: dataset}`` per entry.
        names : list of str
            The artifact each entry was fitted under, in the same order.
        preprocessing : PersistedPreprocessing
            Where the artifacts live and which columns the model reads.
        output_columns : list of str
            The target columns, which every entry carries alongside its
            inputs (see ``_prepare``).

        Returns
        -------
        tuple
            ``(x_entries, y_entries)``: the entries transformed and narrowed
            to the columns the input refs resolve to against that entry's own
            fit, and the matching target. The target is taken from the
            transformed data, not from the splitter's ``y``: it travels
            through the chain with the inputs, so a step that changes rows
            (a resampler on train, NanRemover on every partition) changes
            both together. No converter transforms the target itself (it is
            never part of a scope), so without such steps it is the same
            target the splitter produced.

        Raises
        ------
        JobError
            If an artifact cannot be applied, or preprocessing left a
            partition with a different number of input and target rows.
        """
        import os
        import pickle

        from DashAI.back.preprocessing.column_ref import resolve_refs

        x_entries, y_entries = [], []
        for entry, name in zip(entries, names, strict=True):
            artifact = os.path.join(preprocessing.artifacts_path, f"{name}.pkl")
            try:
                with open(artifact, "rb") as file:
                    preprocessor = pickle.load(file)
                transformed = preprocessor.transform_only(entry)
                input_columns = resolve_refs(
                    preprocessing.input_refs,
                    preprocessor.resolved_columns,
                    preprocessor.resolved_slots,
                )
                x_entry, y_entry = {}, {}
                for partition, dataset in transformed.items():
                    x_entry[partition] = dataset.select_columns(input_columns)
                    y_entry[partition] = dataset.select_columns(output_columns)
            except Exception as e:
                log.exception(e)
                raise JobError(
                    f"Error applying the preprocessing fitted for {name} "
                    f"from {artifact}: {e}",
                ) from e
            for partition in x_entry:
                if x_entry[partition].num_rows != y_entry[partition].num_rows:
                    raise JobError(
                        f"Preprocessing left {x_entry[partition].num_rows} input "
                        f"rows but {y_entry[partition].num_rows} target rows in "
                        f"the '{partition}' partition of {name}."
                    )
            x_entries.append(x_entry)
            y_entries.append(y_entry)
        return x_entries, y_entries

    def _split(self, x: "DashAIDataset", y: "DashAIDataset"):
        """Partition the pair with the configured splitter.

        The splitter's own complaint is passed through as the whole message,
        undecorated. It already names the numbers that explain the refusal --
        how many folds against how many rows -- and a caller that wants to say
        which run this was frames it from outside, which is how the message
        the user reads is built today.
        """
        splitter = self._resolve_splitter()
        try:
            return splitter.split(x, y)
        except JobError:
            raise
        except Exception as e:
            log.exception(e)
            raise JobError(str(e)) from e
