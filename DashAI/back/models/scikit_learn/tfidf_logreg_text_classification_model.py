"""DashAI TF-IDF + Logistic Regression text classification model."""

from typing import TYPE_CHECKING, Union

from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    Lte,
    bool_field,
    enum_field,
    float_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.text_classification_model import TextClassificationModel

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class TfIdfLogRegTextClassificationModelSchema(BaseSchema):
    """Configuration schema for TF-IDF + Logistic Regression text classifier."""

    ngram_min_n: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="Minimum n-gram size for the TF-IDF vectorizer (≥ 1).",
            es="Tamaño mínimo de n-grama para el vectorizador TF-IDF (≥ 1).",
            pt="Tamanho mínimo de n-grama para o vetorizador TF-IDF (≥ 1).",
            de="Minimale N-Gramm-Größe für den TF-IDF-Tokenisierer (≥ 1).",
            zh="TF-IDF 向量化器的最小 n-gram 大小（≥ 1）。",
        ),
        alias=MultilingualString(
            en="Min n-gram",
            es="N-grama mínimo",
            pt="N-grama mínimo",
            de="Minimales N-Gramm",
            zh="最小 n-gram",
        ),
    )  # type: ignore
    ngram_max_n: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en="Maximum n-gram size for the TF-IDF vectorizer (≥ 1).",
            es="Tamaño máximo de n-grama para el vectorizador TF-IDF (≥ 1).",
            pt="Tamanho máximo de n-grama para o vetorizador TF-IDF (≥ 1).",
            de="Maximale N-Gramm-Größe für den TF-IDF-Tokenisierer (≥ 1).",
            zh="TF-IDF 向量化器的最大 n-gram 大小（≥ 1）。",
        ),
        alias=MultilingualString(
            en="Max n-gram",
            es="N-grama máximo",
            pt="N-grama máximo",
            de="Maximales N-Gramm",
            zh="最大 n-gram",
        ),
    )  # type: ignore
    use_idf: schema_field(
        bool_field(),
        placeholder=True,
        description=MultilingualString(
            en="Enable inverse-document-frequency re-weighting.",
            es="Activar re-ponderación por frecuencia inversa de documento.",
            pt="Ativar re-ponderação por frequência inversa de documento.",
            de="Inverse-Dokumenten-Häufigkeits-Neugewichtung aktivieren.",
            zh="启用逆文档频率重加权。",
        ),
        alias=MultilingualString(
            en="Use IDF",
            es="Usar IDF",
            pt="Usar IDF",
            de="IDF verwenden",
            zh="使用 IDF",
        ),
    )  # type: ignore
    sublinear_tf: schema_field(
        bool_field(),
        placeholder=False,
        description=MultilingualString(
            en=("Apply sublinear TF scaling (replace TF with 1 + log(TF))."),
            es=("Aplicar escalado sublineal de TF (reemplazar TF con 1 + log(TF))."),
            pt=(
                "Aplicar escalonamento sublinear de TF (substituir TF por 1 + log(TF))."
            ),
            de=("Sublineare TF-Skalierung anwenden (TF durch 1 + log(TF) ersetzen)."),
            zh="应用次线性 TF 缩放（将 TF 替换为 1 + log(TF)）。",
        ),
        alias=MultilingualString(
            en="Sublinear TF",
            es="TF sublineal",
            pt="TF sublinear",
            de="Sublineares TF",
            zh="次线性 TF",
        ),
    )  # type: ignore
    C: schema_field(
        float_field(gt=0.0),
        placeholder=1.0,
        description=MultilingualString(
            en=(
                "Regularization parameter for logistic regression. "
                "Smaller values mean stronger regularization."
            ),
            es=(
                "Parámetro de regularización para regresión logística. "
                "Valores más pequeños significan mayor regularización."
            ),
            pt=(
                "Parâmetro de regularização para regressão logística. "
                "Valores menores significam regularização mais forte."
            ),
            de=(
                "Regularisierungsparameter für die Logistische Regression. "
                "Kleinere Werte bedeuten stärkere Regularisierung."
            ),
            zh="逻辑回归的正则化参数。值越小，正则化越强。",
        ),
        alias=MultilingualString(
            en="C (Regularization)",
            es="C (Regularización)",
            pt="C (Regularização)",
            de="C (Regularisierung)",
            zh="C（正则化）",
        ),
    )  # type: ignore
    max_iter: schema_field(
        int_field(ge=100),
        placeholder=1000,
        description=MultilingualString(
            en="Maximum number of iterations for the logistic regression solver.",
            es=("Número máximo de iteraciones para el solver de regresión logística."),
            pt="Número máximo de iterações para o solucionador de regressão logística.",
            de="Maximale Iterationen für den Löser der Logistischen Regression.",
            zh="逻辑回归求解器的最大迭代次数。",
        ),
        alias=MultilingualString(
            en="Max iterations",
            es="Iteraciones máximas",
            pt="Iterações máximas",
            de="Maximale Iterationen",
            zh="最大迭代次数",
        ),
    )  # type: ignore
    solver: schema_field(
        enum_field(["lbfgs", "liblinear", "saga"]),
        placeholder="lbfgs",
        description=MultilingualString(
            en="Optimization algorithm for logistic regression.",
            es="Algoritmo de optimización para regresión logística.",
            pt="Algoritmo de otimização para regressão logística.",
            de="Optimierungsalgorithmus für die Logistische Regression.",
            zh="逻辑回归的优化算法。",
        ),
        alias=MultilingualString(
            en="Solver", es="Solver", pt="Solver", de="Löser", zh="求解器"
        ),
    )  # type: ignore

    # A range the underlying library takes as one tuple, which the schema
    # cannot express, so it is split into two fields. sklearn: "Invalid value for
    # ngram_range ... lower boundary larger than upper"; equal is fine.
    rules = [
        Check(
            Lte("ngram_min_n", "ngram_max_n"),
            id="tfidf_logreg.ngram_range_is_ordered",
            targets=["ngram_min_n", "ngram_max_n"],
            message=MultilingualString(
                en="The minimum n-gram size cannot be greater than the maximum.",
                es="El tamaño mínimo de n-grama no puede ser mayor que el máximo.",
                pt="O tamanho mínimo de n-grama não pode ser maior que o máximo.",
                de=(
                    "Die minimale n-Gramm-Größe darf nicht größer als die maximale "
                    "sein."
                ),
                zh="最小n元语法大小不能大于最大值。",
            ),
        ),
    ]


class TfIdfLogRegTextClassificationModel(TextClassificationModel):
    """TF-IDF vectorizer combined with Logistic Regression for text classification.

    This model converts raw text into TF-IDF feature vectors using scikit-learn's
    ``TfidfVectorizer`` with a configurable n-gram range and IDF weighting, then
    trains a ``LogisticRegression`` classifier on the resulting sparse matrix.
    It is a strong baseline for text classification tasks, particularly when
    training data is limited or computational resources are constrained.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.TfidfVectorizer.html
    - [2] https://scikit-learn.org/stable/modules/generated/sklearn.linear_model.LogisticRegression.html
    """

    DISPLAY_NAME: str = MultilingualString(
        en="TF-IDF + Logistic Regression",
        es="TF-IDF + Regresión Logística",
        pt="TF-IDF + Regressão Logística",
        de="TF-IDF + Logistische Regression",
        zh="TF-IDF + 逻辑回归",
    )
    DESCRIPTION: str = MultilingualString(
        en=(
            "TF-IDF vectorizer combined with logistic regression "
            "for text classification."
        ),
        es=(
            "Vectorizador TF-IDF combinado con regresión logística "
            "para clasificación de texto."
        ),
        pt=(
            "Vetorizador TF-IDF combinado com regressão logística "
            "para classificação de texto."
        ),
        de=(
            "TF-IDF-Tokenisierer kombiniert mit Logistischer Regression "
            "für Textklassifikation."
        ),
        zh="TF-IDF 向量化器与逻辑回归结合进行文本分类。",
    )
    COLOR: str = "#00695C"
    ICON: str = "Article"
    SCHEMA = TfIdfLogRegTextClassificationModelSchema

    def __init__(self, **kwargs) -> None:
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.linear_model import LogisticRegression
        from sklearn.preprocessing import LabelEncoder

        self.vectorizer = TfidfVectorizer(
            ngram_range=(kwargs["ngram_min_n"], kwargs["ngram_max_n"]),
            use_idf=kwargs["use_idf"],
            sublinear_tf=kwargs["sublinear_tf"],
        )
        self.classifier = LogisticRegression(
            C=kwargs["C"],
            max_iter=kwargs["max_iter"],
            solver=kwargs["solver"],
        )
        self.label_encoder = LabelEncoder()

    def train(
        self,
        x,
        y,
        x_validation=None,
        y_validation=None,
    ):
        input_col = x.column_names[0]
        output_col = y.column_names[0]

        X_tfidf = self.vectorizer.fit_transform(x[input_col])
        y_enc = self.label_encoder.fit_transform(y[output_col])
        self.classifier.fit(X_tfidf, y_enc)

    def predict(self, x):
        input_col = x.column_names[0]
        X_tfidf = self.vectorizer.transform(x[input_col])
        return self.classifier.predict_proba(X_tfidf)

    def prepare_output(self, dataset: "DashAIDataset", is_fit: bool = False):
        """Label encode the target column, keeping it typed.

        Parameters
        ----------
        dataset : DashAIDataset
            The output dataset containing the target labels.
        is_fit : bool, optional
            If ``True``, fit the label encoder before transforming. If
            ``False``, apply the existing encoding. Default is ``False``.

        Returns
        -------
        DashAIDataset
            The dataset with the target column encoded as integers and typed
            as ``Categorical``, its categories in label encoder order (the
            class index order of the model predictions).
        """
        import pyarrow as pa

        from DashAI.back.dataloaders.classes.dashai_dataset import modify_table
        from DashAI.back.types.categorical import Categorical

        col = dataset.column_names[0]
        if is_fit:
            encoded = self.label_encoder.fit_transform(dataset[col]).tolist()
        else:
            encoded = self.label_encoder.transform(dataset[col]).tolist()

        # Rebuilding the dataset from the encoded values alone would drop the
        # column type, and explainers read the class names from it.
        types = dict(dataset.types)
        types[col] = Categorical(
            values=[str(label) for label in self.label_encoder.classes_],
            converted=True,
        )
        return modify_table(
            dataset,
            columns={col: pa.array(encoded, type=pa.int64())},
            types=types,
        )

    def save(self, filename: Union[str, "Path"]) -> None:
        import joblib

        joblib.dump(self, filename)

    @staticmethod
    def load(filename: Union[str, "Path"]):
        import joblib

        return joblib.load(filename)
