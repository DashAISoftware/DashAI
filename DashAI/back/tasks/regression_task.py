from DashAI.back.core.utils import MultilingualString
from DashAI.back.tasks.supervised_task import SupervisedTask
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float, Integer


class RegressionTask(SupervisedTask):
    """Abstract base task for continuous-output (regression) problems in DashAI.

    Regression tasks predict one or more continuous numeric values from input
    features. This base class constrains output columns to ``Float`` or
    ``Integer`` types and accepts ``Float``, ``Integer``, and ``Categorical``
    input types. Unlike classification tasks, regression does not require a
    ``Categorical`` output and ``num_labels`` always returns ``None``.
    """

    DESCRIPTION: str = MultilingualString(
        en="Predict continuous numeric values from tabular data.",
        es="Predice valores numéricos continuos a partir de datos tabulares.",
        pt="Prevê valores numéricos contínuos a partir de dados tabulares.",
        de="Kontinuierliche numerische Werte aus tabellarischen Daten vorhersagen.",
        zh="从表格数据中预测连续数值。",
    )
    DISPLAY_NAME: str = MultilingualString(
        en="Regression", es="Regresión", pt="Regressão", de="Regression", zh="回归"
    )

    metadata: dict = {
        "inputs_types": [Float, Integer, Categorical],
        "outputs_types": [Float, Integer],
        "inputs_cardinality": "n",
        "outputs_cardinality": 1,
    }
