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
        self._space = None

    def search_space(self, hyperparams_data):
        """
        Configure the search space.

        Parameters
        ----------
        hyperparams_data : list
            Tuples of (obj, hyperparameter, values, dtype) describing the
            search space: a ``(low, high)`` pair for a numeric parameter, and
            the list of options for a categorical one.

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
            elif dtype == "categorical":
                # `values` is the list of options. Note that `hp.choice`
                # reports the *index* of the chosen option in everything
                # hyperopt hands back afterwards, which is why the results are
                # read through `space_eval` rather than coerced by dtype.
                search_space[hyperparameter] = hp.choice(hyperparameter, values)
            else:
                # Previously this loop had no else, so a parameter of any other
                # kind was left out of the space and silently never optimized:
                # the study ran, reported trials, and moved nothing.
                raise TypeError(
                    f"Unsupported parameter type for {hyperparameter} : {dtype}"
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
        # Kept so the results can be read back through it: hyperopt reports the
        # internal representation of a point, and for `hp.choice` that is an
        # index into the options rather than the option itself.
        self._space = search_space

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
        for param_name, value in self._decode(best_params_raw).items():
            obj, key, _dtype = param_mapping[param_name]
            setattr(obj, key, value)

    def get_model(self):
        return self.model

    def _decode(self, raw_values: dict) -> dict:
        """Turn hyperopt's internal representation of a point into real values.

        For a numeric parameter the raw value is the value, give or take the
        float that ``hp.quniform`` returns where an integer is wanted. For a
        categorical one it is the *index* of the chosen option, so reading it as
        a number yields ``1.0`` where the model expects ``"hinge"``.
        ``space_eval`` resolves the point against the space that produced it,
        which is right for both.
        """
        from hyperopt import space_eval

        values = space_eval(self._space, raw_values)
        dtypes = {key: dtype for _, key, _, dtype in self.parameters}
        return {
            key: int(value)
            if dtypes.get(key) == "integer"
            else float(value)
            if dtypes.get(key) == "number"
            else value
            for key, value in values.items()
        }

    def get_trials_values(self):
        trials = []
        for trial in self.trials:
            if trial["result"]["status"] == "ok":
                params = self._decode(
                    {key: val[0] for key, val in trial["misc"]["vals"].items()}
                )
                loss = trial["result"]["loss"]
                value = -loss if self.maximize else loss
                trials.append({"params": params, "value": value})
        return trials

    def get_best_params(self):
        """Return the best parameters found during optimization."""
        best_trial = min(
            self.trials, key=lambda t: t["result"].get("loss", float("inf"))
        )
        return self._decode(
            {key: vals[0] for key, vals in best_trial["misc"]["vals"].items()}
        )
