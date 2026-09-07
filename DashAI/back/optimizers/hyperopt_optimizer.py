from DashAI.back.core.schema_fields import (
    BaseSchema,
    enum_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.optimizers.base_optimizer import BaseOptimizer


class HyperOptSchema(BaseSchema):
    n_trials: schema_field(
        int_field(gt=0),
        placeholder=10,
        description=MultilingualString(
            en=(
                "The quantity of trials per study. It must be of type positive integer."
            ),
            es=("La cantidad de pruebas por estudio. Debe ser un entero positivo."),
            pt=("A quantidade de tentativas por estudo. Deve ser um inteiro positivo."),
            de=(
                "Die Anzahl der Versuche pro Studie. Muss eine positive ganze Zahl "
                "sein."
            ),
            zh="每次研究的试验次数，必须为正整数。",
        ),
        alias=MultilingualString(
            en="N trials",
            es="N pruebas",
            pt="N tentativas",
            de="N Versuche",
            zh="试验次数",
        ),
    )  # type: ignore
    sampler: schema_field(
        enum_field(enum=["tpe", "rand"]),
        placeholder="tpe",
        description=MultilingualString(
            en=(
                "The sampler algorithm to use for hyperparameter optimization. "
                "Must be 'tpe' (Tree-structured Parzen Estimator) or 'rand' (Random)."
            ),
            es=(
                "El algoritmo de muestreo a usar para la optimización de "
                "hiperparámetros. Debe ser 'tpe' (Tree-structured Parzen Estimator) "
                "o 'rand' (Aleatorio)."
            ),
            pt=(
                "O algoritmo de amostragem a usar para a otimização de "
                "hiperparâmetros. Deve ser 'tpe' (Tree-structured Parzen Estimator) "
                "ou 'rand' (Aleatório)."
            ),
            de=(
                "Der Abtastalgorithmus für die Hyperparameter-Optimierung. "
                "Muss 'tpe' (Tree-structured Parzen Estimator) oder 'rand' (Zufällig) "
                "sein."
            ),
            zh=(
                "用于超参数优化的采样算法。"
                "必须为 'tpe'（树形结构 Parzen 估计器）或 'rand'（随机）。"
            ),
        ),
        alias=MultilingualString(
            en="Sampler",
            es="Muestreador",
            pt="Amostrador",
            de="Abtaster",
            zh="采样器",
        ),
    )  # type: ignore


class HyperOptOptimizer(BaseOptimizer):
    DISPLAY_NAME: str = MultilingualString(
        en="HyperOpt Optimizer",
        es="Optimizador HyperOpt",
        pt="Otimizador HyperOpt",
        de="HyperOpt-Optimierer",
        zh="HyperOpt 优化器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Hyperparameter optimization using HyperOpt library.",
        es="Optimización de hiperparámetros usando la librería HyperOpt.",
        pt="Otimização de hiperparâmetros usando a biblioteca HyperOpt.",
        de="Hyperparameter-Optimierung mit der HyperOpt-Bibliothek.",
        zh="使用 HyperOpt 库进行超参数优化。",
    )
    COLOR: str = "#FF5722"
    SCHEMA = HyperOptSchema

    COMPATIBLE_COMPONENTS = [
        "TabularClassificationTask",
        "TextClassificationTask",
        "TranslationTask",
    ]

    def __init__(self, n_trials=None, sampler=None):
        self.n_trials = n_trials
        self.sampler = sampler

    def search_space(self, hyperparams_data):
        """
        Configure the search space.

        Parameters
        ----------
        hyperparams_data : list
            Tuples of (obj, hyperparameter, values, dtype) describing the
            search space bounds.

        Returns
        -------
        dict
            Search space dict compatible with hyperopt.
        """
        from hyperopt import hp

        search_space = {}

        for _, hyperparameter, values, dtype in hyperparams_data:
            if dtype == "integer":
                search_space[hyperparameter] = hp.quniform(
                    hyperparameter, values[0], values[1], 1
                )
            elif dtype == "number":
                search_space[hyperparameter] = hp.uniform(
                    hyperparameter, values[0], values[1]
                )

        return search_space

    def optimize(
        self, model, input_dataset, output_dataset, parameters, metric, strategy
    ):
        """
        Run hyperparameter optimization.

        Parameters
        ----------
        model : object
            Model instance to optimize.
        input_dataset : dict
            Dataset splits keyed by "train" and "validation".
        output_dataset : dict
            Label splits keyed by "train" and "validation".
        parameters : list
            Tuples of (obj, key, bounds, dtype) for each hyperparameter.
        metric : dict
            Dict with keys "class" (metric instance) and "metadata".
        strategy : callable
            Function that trains the model and returns a score based on the metric.
            Depends on the specific evaluation strategy used.
        """
        import importlib

        from hyperopt import Trials, fmin

        self.model = model
        self.input_dataset = input_dataset
        self.output_dataset = output_dataset
        self.parameters = parameters
        self.metric = metric["class"]
        self.maximize = metric["metadata"]["maximize"]

        sampler = importlib.import_module(f"hyperopt.{self.sampler}").suggest

        param_mapping = {
            key: (obj, key, dtype) for obj, key, _, dtype in self.parameters
        }

        search_space = self.search_space(self.parameters)

        def objective(params):
            for param_name, value in params.items():
                obj, key, dtype = param_mapping[param_name]
                if dtype == "integer":
                    value = int(value)
                elif dtype == "number":
                    value = float(value)
                setattr(obj, key, value)

            # Delegate evaluation entirely to strategy, identical to Optuna
            score = strategy(
                self.model, self.input_dataset, self.output_dataset, self.metric
            )

            # fmin always minimizes, so negate when the metric should be maximized
            return -score if self.maximize else score

        trials = Trials()
        best_params_raw = fmin(
            fn=objective,
            space=search_space,
            algo=sampler,
            max_evals=self.n_trials,
            trials=trials,
        )
        self.trials = trials

        # Apply best params and retrain with the best configuration
        for param_name, raw_value in best_params_raw.items():
            obj, key, dtype = param_mapping[param_name]
            value = int(raw_value) if dtype == "integer" else float(raw_value)
            setattr(obj, key, value)

    def get_model(self):
        return self.model

    def get_trials_values(self):
        trials = []
        for trial in self.trials:
            if trial["result"]["status"] == "ok":
                params = {key: val[0] for key, val in trial["misc"]["vals"].items()}
                loss = trial["result"]["loss"]
                value = -loss if self.maximize else loss
                trials.append({"params": params, "value": value})
        return trials

    def get_best_params(self):
        """Return the best parameters found during optimization."""
        best_trial = min(
            self.trials, key=lambda t: t["result"].get("loss", float("inf"))
        )
        param_mapping = {
            key: (obj, key, dtype) for obj, key, _, dtype in self.parameters
        }
        result = {}
        for key, vals in best_trial["misc"]["vals"].items():
            raw = vals[0]
            dtype = param_mapping[key][2]
            result[key] = int(raw) if dtype == "integer" else float(raw)
        return result
