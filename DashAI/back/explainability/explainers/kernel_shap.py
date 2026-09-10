import re
from typing import List, Optional

from DashAI.back.core.artifacts import (
    ArtifactGroup,
    GroupedArtifacts,
    PlotlyArtifact,
)
from DashAI.back.core.schema_fields import (
    BaseSchema,
    bool_field,
    enum_field,
    float_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.explainability.local_explainer import BaseLocalExplainer
from DashAI.back.explainability.story import format_story
from DashAI.back.models.base_model import BaseModel
from DashAI.back.types.categorical import Categorical


class KernelShapSchema(BaseSchema):
    """Schema for KernelShap explainer hyperparameters.

    Configures the link function that connects SHAP feature-attribution values to
    the model output scale (``"identity"`` for regression/probability outputs,
    ``"logit"`` for log-odds interpretation), and the background-data fraction
    used to estimate the expected model output.
    """

    link: schema_field(
        enum_field(enum=["identity", "logit"]),
        placeholder="identity",
        description=MultilingualString(
            en=(
                "Link function to connect feature importance values to the "
                "model's outputs. Options are 'identity' (identity function) "
                "or 'logit' (log-odds)."
            ),
            es=(
                "Función de enlace para conectar los valores de importancia de "
                "características con las salidas del modelo. Opciones: 'identity' "
                "(identidad) o 'logit' (log-odds)."
            ),
            pt=(
                "Função de ligação para conectar os valores de importância das "
                "características às saídas do modelo. Opções: 'identity' "
                "(identidade) ou 'logit' (log-odds)."
            ),
            zh=(
                "将特征重要性值连接到模型输出的链接函数。"
                "选项：'identity'（恒等函数）或'logit'（对数几率）。"
            ),
            de=(
                "Verknüpfungsfunktion, um Merkmalswichtigkeitswerte mit den "
                "Modellausgaben zu verbinden. Optionen: 'identity' "
                "(Identitätsfunktion) oder 'logit' (Log-Odds)."
            ),
        ),
        alias=MultilingualString(
            en="Link function",
            es="Función de enlace",
            pt="Função de ligação",
            zh="链接函数",
            de="Verknüpfungsfunktion",
        ),
    )  # type: ignore

    fit_parameter_sample_background_data: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en=(
                "Parameter to fit the explainer. 'true' if background data must "
                "be sampled; otherwise the entire training set is used. Smaller "
                "datasets speed up the algorithm runtime."
            ),
            es=(
                "Parámetro para ajustar el explicador. 'true' si se deben "
                "muestrear los datos de fondo; de lo contrario se usa el "
                "conjunto de entrenamiento completo. Conjuntos más pequeños "
                "reducen el tiempo de ejecución."
            ),
            pt=(
                "Parâmetro para ajustar o explicador. 'true' se os dados de "
                "fundo devem ser amostrados; caso contrário, usa-se o conjunto "
                "de treinamento completo. Conjuntos menores reduzem o tempo de "
                "execução."
            ),
            zh=(
                "用于拟合解释器的参数。如果需要对背景数据进行采样则为'true'；"
                "否则使用整个训练集。较小的数据集可加速算法运行时间。"
            ),
            de=(
                "Parameter zum Anpassen des Erklärers. 'true', wenn Hintergrunddaten "
                "gesamplet werden müssen; sonst wird der gesamte Trainingssatz "
                "verwendet. Kleinere Datensätze beschleunigen die Laufzeit."
            ),
        ),
        alias=MultilingualString(
            en="Sample background data",
            es="Muestrear datos de fondo",
            pt="Amostrar dados de fundo",
            zh="采样背景数据",
            de="Hintergrunddaten samplen",
        ),
    )  # type: ignore

    fit_parameter_background_fraction: schema_field(
        float_field(ge=0, le=1),
        placeholder=0.2,
        description=MultilingualString(
            en=(
                "If 'Sample background data' is selected, this corresponds to "
                "the fraction of background samples to draw from the training set."
            ),
            es=(
                "Si se selecciona 'Muestrear datos de fondo', entonces corresponde "
                "a la proporción de muestras de fondo a extraer "
                "del conjunto de entrenamiento."
            ),
            pt=(
                "Se 'Amostrar dados de fundo' estiver selecionado, corresponde "
                "à fração de amostras de fundo a extrair do conjunto de "
                "treinamento."
            ),
            zh="如果选择了'采样背景数据'，则对应从训练集中抽取的背景样本比例。",
            de=(
                "Wenn 'Hintergrunddaten samplen' ausgewählt ist, entspricht dies dem "
                "Anteil der Hintergrundproben aus dem Trainingssatz."
            ),
        ),
        alias=MultilingualString(
            en="Background fraction",
            es="Fracción de fondo",
            pt="Fração de fundo",
            zh="背景比例",
            de="Hintergrundfraktion",
        ),
    )  # type: ignore

    fit_parameter_sampling_method: schema_field(
        enum_field(enum=["shuffle", "kmeans"]),
        placeholder="shuffle",
        description=MultilingualString(
            en=(
                "If 'true', choose to sample random "
                "instances with 'shuffle' or summarize the dataset with "
                "'kmeans'. If there are categorical features, 'shuffle' is used "
                "by default."
            ),
            es=(
                "Si es 'true', elija muestrear "
                "instancias aleatorias con 'shuffle' o resumir el conjunto con "
                "'kmeans'. Si hay características categóricas, se usa 'shuffle' "
                "por defecto."
            ),
            pt=(
                "Se for 'true', escolha amostrar instâncias aleatórias com "
                "'shuffle' ou resumir o conjunto de dados com 'kmeans'. Se "
                "houver características categóricas, 'shuffle' é usado por "
                "padrão."
            ),
            zh=(
                "如果为'true'，选择用'shuffle'随机采样实例或用'kmeans'汇总数据集。"
                "如果存在类别特征，默认使用'shuffle'。"
            ),
            de=(
                "Wenn 'true', werden zufällige Instanzen mit 'shuffle' gesamplet "
                "oder der Datensatz mit 'kmeans' zusammengefasst. Bei kategorialen "
                "Merkmalen wird standardmäßig 'shuffle' verwendet."
            ),
        ),
        alias=MultilingualString(
            en="Sampling method",
            es="Método de muestreo",
            pt="Método de amostragem",
            zh="采样方法",
            de="Samplingmethode",
        ),
    )  # type: ignore


class KernelShap(BaseLocalExplainer):
    """Model agnostic local explainer that estimates SHAP values
    via a weighted linear model.

    Kernel SHAP (SHapley Additive exPlanations) unifies LIME and classic Shapley
    values from cooperative game theory. For each instance to explain, it fits a
    weighted linear model over a sampled coalition of feature subsets, where the
    sample weights are derived from the Shapley kernel. The resulting coefficients
    are the SHAP values. Each one represents the marginal contribution of a feature
    to the model's prediction relative to a background (reference) distribution.

    Because it treats the model as a black box (querying only ``predict_proba``),
    Kernel SHAP works with any classifier. The trade-off is higher computational
    cost compared to model-specific SHAP implementations (Tree SHAP, Deep SHAP).

    References
    ----------
    - [1] Lundberg, S.M. & Lee, S.I. (2017). "A Unified Approach to Interpreting
           Model Predictions." NeurIPS 30. https://arxiv.org/abs/1705.07874
    - [2] https://shap.readthedocs.io/en/latest/generated/shap.KernelExplainer.html
    """

    COMPATIBLE_COMPONENTS = ["TabularClassificationTask"]
    DISPLAY_NAME = MultilingualString(
        en="Kernel SHAP",
        es="Kernel SHAP",
        pt="Kernel SHAP",
        zh="Kernel SHAP",
        de="Kernel SHAP",
    )
    DESCRIPTION = MultilingualString(
        en=(
            "Kernel SHAP approximates SHAP values to explain a model's output by "
            "attributing contributions of each feature to the prediction."
        ),
        es=(
            "Kernel SHAP aproxima los valores SHAP para explicar la salida del "
            "modelo atribuyendo la contribución de cada característica a la "
            "predicción."
        ),
        pt=(
            "Kernel SHAP aproxima os valores de Shapley para explicar a saída do "
            "modelo atribuindo a contribuição de cada característica à previsão."
        ),
        zh=("Kernel SHAP通过将每个特征的贡献归因于预测来逼近SHAP值，以解释模型输出。"),
        de=(
            "Kernel SHAP approximiert SHAP-Werte, um die Modellausgabe zu erklären, "
            "indem die Beiträge jedes Merkmals zur Vorhersage zugeordnet werden."
        ),
    )
    COLOR = "#008000"
    SCHEMA = KernelShapSchema

    def __init__(
        self,
        model: BaseModel,
        link: str = "identity",
    ):
        """Initialize a new instance of a KernelShap explainer.

        Parameters
        ----------
        model: BaseModel
                Model to be explained.
        link: str
            String indicating the link function to connect the feature importance
            values to the model's outputs. Options are 'identity' to use identity
            function or 'logit'to use log-odds function.
        """
        super().__init__(model)
        self.link = link

    def _sample_background_data(
        self,
        background_data,
        background_fraction: float,
        sampling_method: str = "shuffle",
        categorical_features: bool = False,
    ):
        """Method to sample the background dataset used to fit the explainer.


        Parameters
        ----------
        background_data: np.array
            Data used to estimate feature attributions and establish a baseline for
            the calculation of SHAP values.
        background_fraction: float
            Proportion of background data samples used to estimate of SHAP values. By
            default, the entire train dataset is used, but this option limits the
            samples to reduce run times.
        sampling_method: str
            Sampling method used to select the background samples. Options are
            'shuffle' to select random samples or 'kmeans' to summarise the data
            set. 'kmeans' option can only be used if there are no categorical
            features.
        categorical_features: bool
            Bool indicating whether some features are categorical.

        Returns
        -------
        pd.DataFrame
            pandas DataFrame with the background data used to fit the
            explainer.
        """

        # Lazy import of shap to avoid heavy imports at module load time
        import shap

        samplers = {"shuffle": shap.sample, "kmeans": shap.kmeans}

        n_background_samples = int(background_fraction * background_data.shape[0])

        if categorical_features:
            data = samplers["shuffle"](background_data, n_background_samples)
        else:
            data = samplers[sampling_method](background_data, n_background_samples)

        return data

    def fit(
        self,
        background_dataset,
        sample_background_data="false",
        background_fraction=None,
        sampling_method=None,
    ):
        """Method to train the KernelShap explainer.

        Parameters
        ----------
        background_data: Tuple[DatasetDict, DatasetDict]
            Tuple with (input_samples, targets). Input samples are used to estimate
            feature attributions and establish a baseline for the calculation of
            SHAP values.
        sample_background_data: bool
            True if the background data must be sampled. Smaller data sets speed up
            the algorithm run time. False by default.
        background_fraction: float
            Proportion of background data from the training samples used to estimate
            SHAP values if ``sample_background_data=True``.
        sampling_method: str
            Sampling method used to select the background samples if
            ``sample_background_data=True``. Options are 'shuffle' to select random
            samples or 'kmeans' to summarise the data set. 'kmeans' option can only
            be used if there are no categorical features.

        Returns
        -------
        KernelShap object
        """
        sample_background_data = bool(sample_background_data)

        from DashAI.back.explainability.model_input import prepare_model_input

        x, y = background_dataset

        # SHAP perturbs the background frame and calls the model with it, so
        # the background must already be in the model's feature space and the
        # model must be queried through predict_prepared.
        x_train = prepare_model_input(self.model, x["train"])
        y_train = y["train"]

        background_data = x_train.to_pandas()
        features = x_train.column_names
        types = x_train.types
        feature_names = list(features)

        categorical_features = False
        for feature in features:
            if isinstance(types[feature], Categorical):
                categorical_features = True

        if sample_background_data:
            background_data = self._sample_background_data(
                background_data.to_numpy(),
                background_fraction,
                sampling_method,
                categorical_features,
            )

        # Lazy import of shap
        import shap

        self.explainer = shap.KernelExplainer(
            model=self.model.predict_prepared,
            data=background_data,
            feature_names=feature_names,
            link=self.link,
        )

        # Metadata
        output_column = y_train.column_names[0]
        target_names = y_train.types[output_column].categories
        self.metadata = {"feature_names": feature_names, "target_names": target_names}

        return self

    def explain_instance(
        self,
        instances,
    ):
        """Method for explaining the model prediciton of an instance using the Kernel
        Shap method.

        Parameters
        ----------
        instances: DatasetDict
            Instances to be explained.

        Returns
        -------
        dict
            dictionary with the shap values for each instance.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset
        from DashAI.back.explainability.model_input import prepare_model_input

        dataset_dashai = to_dashai_dataset(instances)
        dataset_prepared = prepare_model_input(self.model, dataset_dashai)

        X = dataset_prepared.to_pandas()

        predictions = self.model.predict(x_pred=dataset_dashai)

        # TODO: evaluate args nsamples y l1_reg
        # Lazy import numpy
        import numpy as np

        shap_values = self.explainer.shap_values(X=X)

        # shap_values has size (n_instances, n_features, n_classes)
        # Reorder shap values: (n_instances, n_classes, n_features)
        shap_values = np.array(shap_values).transpose(0, 2, 1)

        explanation = {
            "metadata": self.metadata,
            "base_values": np.round(self.explainer.expected_value, 3).tolist(),
        }

        for i, (instance, prediction, contribution_values) in enumerate(
            zip(X.to_numpy(), predictions, shap_values)  # noqa B905
        ):
            explanation[i] = {
                "instance_values": instance.tolist(),
                "model_prediction": prediction.tolist(),
                "shap_values": np.round(contribution_values, 3).tolist(),
            }

        return explanation

    def _create_plot(
        self,
        data,
        base_value: float,
        y_pred_pbb: float,
        title: Optional[str] = None,
    ):
        """Helper method to create the explanation plot using plotly.

        Parameters
        ----------
        data: pd.DataFrame
            dataframe containing the data to be plotted.
        base_value: float
            value to set where the bar base is drawn.
        y_pred_pbb: float
            predicted probability.
        title: Optional[str]
            title of the resulting artifact.

        Returns
        -------
        PlotlyArtifact
            The plotly artifact of the explanation plot for one instance.
        """
        # Lazy imports
        import numpy as np
        import plotly.graph_objs as go

        x = data["shap_values"].to_numpy()
        y = data["label"].to_numpy()
        measure = np.repeat("relative", len(y))
        texts = data["shap_values"].to_numpy()

        fig = go.Figure(
            go.Waterfall(
                x=x,
                y=y,
                base=base_value,
                name="20",
                orientation="h",
                measure=measure,
                text=texts,
                textposition="auto",
                constraintext="inside",
                decreasing={"marker": {"color": "rgb(47,138,196)"}},
                increasing={"marker": {"color": "rgb(231,63,116)"}},
            )
        )

        fig.update_layout(
            margin={"pad": 20, "l": 100, "r": 130, "t": 60, "b": 10},
            xaxis={
                "tickangle": -90,
                "tickwidth": 100,
                "title_text": "",
            },
            yaxis={"showgrid": True, "tickwidth": 150},
        )

        fig.update_xaxes(
            gridcolor="#1B2631",
            gridwidth=1,
            tickmode="array",
            nticks=2,
            tickvals=[base_value, y_pred_pbb],
            ticktext=[f"E[f(x)]={base_value}", f"f(x)={y_pred_pbb}"],
            tickangle=0,
            showgrid=True,
        )

        return PlotlyArtifact(payload=fig, title=title)

    def plot(self, explanation: dict) -> List[GroupedArtifacts]:
        """Method to create the explanation plots using plotly.

        Parameters
        ----------
        explanation : dict
            Dictionary with the explanation generated by the explainer.

        Returns
        -------
        List[GroupedArtifacts]
            A single grouped artifact with one group ("Instance 1", ...) per
            explained instance, each holding that instance's plotly plot.
        """

        exp = explanation.copy()

        max_features = 8
        metadata = exp.pop("metadata")
        base_values = exp.pop("base_values")
        feature_names = metadata["feature_names"]

        # Normaliza feature_names a 1D
        # Lazy import heavy libs
        import numpy as np
        import pandas as pd

        feats = np.asarray(feature_names, dtype=str).reshape(-1)

        groups = []
        for instance_number, i in enumerate(exp, start=1):
            instance_values = exp[i]["instance_values"]
            model_prediction = exp[i]["model_prediction"]
            y_pred_class = int(np.argmax(model_prediction))
            y_pred_pbb = float(np.round(model_prediction[y_pred_class], 2))

            # --- Normaliza valores de la instancia a 1D
            vals = np.asarray(instance_values).reshape(-1)

            # --- Normaliza shap_values a 1D alineado con feats
            sv = exp[i]["shap_values"]
            # 1) Si viene como lista (típico multiclass: una entrada por clase)
            if isinstance(sv, list):
                sv_raw = np.asarray(sv[y_pred_class])
            else:
                sv_raw = np.asarray(sv)

            # 2) Intenta extraer del objeto shap.Explanation si aplica
            try:
                # Lazy import of shap Explanation type only if available
                from shap._explanation import Explanation

                if isinstance(sv, Explanation):
                    sv_raw = np.asarray(sv.values)
            except Exception:
                pass

            # 3) Resolver formas 2D con eje de clases/características
            if sv_raw.ndim == 2:
                if sv_raw.shape[0] == feats.size and sv_raw.shape[1] != feats.size:
                    # n_features, n_classes
                    sv_raw = sv_raw[:, y_pred_class]
                elif sv_raw.shape[1] == feats.size and sv_raw.shape[0] != feats.size:
                    # n_classes n_features
                    sv_raw = sv_raw[y_pred_class, :]
                elif (
                    sv_raw.shape[0] == 1
                    and sv_raw.shape[1] == feats.size
                    or sv_raw.shape[1] == 1
                    and sv_raw.shape[0] == feats.size
                ):
                    sv_raw = sv_raw.reshape(-1)
                else:
                    raise ValueError(
                        f"shap_values {sv_raw.shape} n_features={feats.size}"
                    )
            else:
                sv_raw = sv_raw.reshape(-1)

            # 4) Asegura mismas longitudes (recorte defensivo si algo llegó desalineado)
            n = min(vals.size, feats.size, sv_raw.size)
            if not (vals.size == feats.size == sv_raw.size):
                # Puedes cambiar este print por un logger si lo prefieres
                print(
                    f"[WARN] Desalineado: len(values)={vals.size}, "
                    f"len(features)={feats.size}, len(shap_values)={sv_raw.size}. "
                    f"Se recorta a {n}."
                )
                vals = vals[:n]
                feats = feats[:n]
                sv_raw = sv_raw[:n]

            # --- Construcción del DataFrame ya normalizado
            data = pd.DataFrame(
                {
                    "values": vals,
                    "shap_values": sv_raw,
                    "features": feats,
                }
            )

            # --- Resto de tu pipeline
            data["shap_values_abs"] = np.abs(data["shap_values"])
            data = data.sort_values(by="shap_values_abs", ascending=True)

            if len(data) > max_features:
                data_1 = data.iloc[-max_features:, :]
                data_2 = data.iloc[:-max_features, :]
                others = pd.DataFrame.from_dict(
                    {
                        "values": [None],
                        "shap_values": [
                            float(np.round(data_2["shap_values"].sum(), 3))
                        ],
                        "shap_values_abs": [None],
                        "features": ["Others"],
                    }
                )
                data = pd.concat([others, data_1], ignore_index=True)

            data["label"] = data["features"] + "=" + data["values"].map(str)

            # base_values puede ser escalar o vector por clase
            base_arr = np.asarray(base_values)
            if base_arr.ndim == 0:
                base_value = float(base_arr)
            else:
                base_value = float(base_arr[y_pred_class])

            plot = self._create_plot(
                data,
                base_value,
                y_pred_pbb,
            )
            groups.append(
                ArtifactGroup(title=f"Instance {instance_number}", artifacts=[plot])
            )

        return [GroupedArtifacts(groups=groups)]

    def story(
        self, explanation: dict, explainer_output: ArtifactGroup
    ) -> Optional[MultilingualString]:
        """Describe, in words, the prediction and top SHAP contributors.

        Names the predicted class, its probability, and the top-3 features
        by absolute SHAP value for the predicted class (the same values
        plotted by :meth:`plot`).

        Parameters
        ----------
        explanation : dict
            Output of :meth:`explain_instance`.
        explainer_output : ArtifactGroup
            The group previously returned by :meth:`plot`, titled
            ``"Instance {n}"``.

        Returns
        -------
        Optional[MultilingualString]
            The narrative in every supported language, or ``None`` if
            ``explainer_output`` is not a recognised "Instance N" group.
        """
        match = re.match(r"Instance (\d+)", explainer_output.title or "")
        if match is None:
            return None
        index = int(match.group(1)) - 1
        if index not in explanation:
            return None

        # Lazy import
        import numpy as np

        feature_names = explanation["metadata"]["feature_names"]
        target_names = explanation["metadata"]["target_names"]
        instance = explanation[index]

        model_prediction = np.asarray(instance["model_prediction"])
        predicted_class = int(np.argmax(model_prediction))
        predicted_name = target_names[predicted_class]
        predicted_prob = float(model_prediction[predicted_class])

        class_shap_values = np.asarray(instance["shap_values"])[predicted_class]
        ranking = sorted(
            zip(feature_names, class_shap_values, strict=True),
            key=lambda pair: abs(pair[1]),
            reverse=True,
        )
        top = ranking[:3]
        feature_list = ", ".join(f"{name} ({value:+.3f})" for name, value in top)

        return format_story(
            {
                "en": (
                    "The model predicted '{predicted_name}' with probability "
                    "{predicted_prob:.2f}. The features that contributed most "
                    "to this prediction (SHAP values) were: {feature_list}; "
                    "positive values push the prediction toward "
                    "'{predicted_name}', negative values push it away."
                ),
                "es": (
                    "El modelo predijo '{predicted_name}' con probabilidad "
                    "{predicted_prob:.2f}. Las características que más "
                    "contribuyeron a esta predicción (valores SHAP) fueron: "
                    "{feature_list}; los valores positivos empujan la "
                    "predicción hacia '{predicted_name}', los negativos la "
                    "alejan."
                ),
                "pt": (
                    "O modelo previu '{predicted_name}' com probabilidade "
                    "{predicted_prob:.2f}. As características que mais "
                    "contribuíram para essa previsão (valores SHAP) foram: "
                    "{feature_list}; valores positivos empurram a previsão "
                    "em direção a '{predicted_name}', valores negativos a "
                    "afastam."
                ),
                "de": (
                    "Das Modell sagte '{predicted_name}' mit einer "
                    "Wahrscheinlichkeit von {predicted_prob:.2f} voraus. Die "
                    "Merkmale, die am meisten zu dieser Vorhersage "
                    "beigetragen haben (SHAP-Werte), waren: {feature_list}; "
                    "positive Werte verstärken die Vorhersage in Richtung "
                    "'{predicted_name}', negative Werte schwächen sie ab."
                ),
                "zh": (
                    "模型预测为'{predicted_name}'，概率为{predicted_prob:.2f}。"
                    "对该预测贡献最大的特征（SHAP值）是：{feature_list}；"
                    "正值表示推动预测趋向'{predicted_name}'，负值表示相反。"
                ),
            },
            predicted_name=predicted_name,
            predicted_prob=predicted_prob,
            feature_list=feature_list,
        )
