from typing import TYPE_CHECKING, Optional, Union

from DashAI.back.core.schema_fields import (
    BaseSchema,
    Check,
    Lte,
    component_field,
    int_field,
    schema_field,
)
from DashAI.back.core.utils import MultilingualString
from DashAI.back.models.text_classification_model import TextClassificationModel
from DashAI.back.types.categorical import Categorical
from DashAI.back.types.value_types import Float

if TYPE_CHECKING:
    from pathlib import Path

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class BagOfWordsTextClassificationModelSchema(BaseSchema):
    """Configuration schema for the Bag-of-Words text classification meta-model.

    Configures the underlying tabular classifier (``tabular_classifier``) and
    the n-gram range for the ``CountVectorizer`` (``ngram_min_n``,
    ``ngram_max_n``) used by ``BagOfWordsTextClassificationModel``.
    """

    tabular_classifier: schema_field(
        component_field(parent="TabularClassificationModel"),
        placeholder={"component": "SVC", "params": {}},
        description=MultilingualString(
            en=(
                "Tabular model used as the underlying model "
                "to generate the text classifier."
            ),
            es=(
                "Modelo tabular usado como el modelo subyacente "
                "para generar el clasificador de texto."
            ),
            pt=(
                "Modelo tabular usado como o modelo subjacente "
                "para gerar o classificador de texto."
            ),
            de=(
                "Tabellarisches Modell, das als zugrunde liegendes Modell "
                "zur Erstellung des Textklassifikators verwendet wird."
            ),
            zh="用作生成文本分类器的底层表格模型。",
        ),
        alias=MultilingualString(
            en="Tabular classifier",
            es="Clasificador tabular",
            pt="Classificador tabular",
            de="Tabellarischer Klassifikator",
            zh="表格分类器",
        ),
    )  # type: ignore
    ngram_min_n: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en=(
                "The lower boundary of the range of n-values for different word "
                "n-grams or char n-grams to be extracted. It must be an integer "
                "greater or equal than 1"
            ),
            es=(
                "El límite inferior del rango de valores n para diferentes n-gramas "
                "de palabras o caracteres a extraer. Debe ser un entero mayor o "
                "igual a 1"
            ),
            pt=(
                "O limite inferior do intervalo de valores n para diferentes n-gramas "
                "de palavras ou caracteres a extrair. Deve ser um inteiro maior ou "
                "igual a 1"
            ),
            de=(
                "Die untere Grenze des Bereichs der n-Werte für verschiedene Wort- "
                "oder Zeichen-N-Gramme. Muss eine ganze Zahl größer oder gleich 1 sein."
            ),
            zh="提取的词n-gram或字符n-gram的n值范围下界，必须为大于等于1的整数。",
        ),
        alias=MultilingualString(
            en="Ngram min N",
            es="Ngrama mínimo N",
            pt="N-grama mínimo N",
            de="N-Gramm min N",
            zh="N-gram 最小 N",
        ),
    )  # type: ignore
    ngram_max_n: schema_field(
        int_field(ge=1),
        placeholder=1,
        description=MultilingualString(
            en=(
                "The upper boundary of the range of n-values for different word "
                "n-grams or char n-grams to be extracted. It must be an integer "
                "greater or equal than 1"
            ),
            es=(
                "El límite superior del rango de valores n para diferentes n-gramas "
                "de palabras o caracteres a extraer. Debe ser un entero mayor o "
                "igual a 1"
            ),
            pt=(
                "O limite superior do intervalo de valores n para diferentes n-gramas "
                "de palavras ou caracteres a extrair. Deve ser um inteiro maior ou "
                "igual a 1"
            ),
            de=(
                "Die obere Grenze des Bereichs der n-Werte für verschiedene Wort- "
                "oder Zeichen-N-Gramme. Muss eine ganze Zahl größer oder gleich 1 sein."
            ),
            zh="提取的词n-gram或字符n-gram的n值范围上界，必须为大于等于1的整数。",
        ),
        alias=MultilingualString(
            en="Ngram max N",
            es="Ngrama máximo N",
            pt="N-grama máximo N",
            de="N-Gramm max N",
            zh="N-gram 最大 N",
        ),
    )  # type: ignore

    # A range the underlying library takes as one tuple, which the schema
    # cannot express, so it is split into two fields. sklearn: "Invalid value for
    # ngram_range ... lower boundary larger than upper"; equal is fine.
    rules = [
        Check(
            Lte("ngram_min_n", "ngram_max_n"),
            id="bow_model.ngram_range_is_ordered",
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


class BagOfWordsTextClassificationModel(TextClassificationModel):
    """
    Text classification meta-model that combines a bag-of-words vectorizer
    with a DashAI tabular classifier.

    The model converts raw text into a token-count matrix using scikit-learn's
    ``CountVectorizer`` with a configurable n-gram range, then passes the
    resulting sparse feature matrix to any DashAI ``TabularClassificationModel``
    for training and prediction. This decouples text featurisation from the
    choice of classifier, allowing any registered DashAI tabular model (tree based,
    SVM, linear, etc.) to be applied to text classification without modification.

    During training the vectorizer is fitted on the input text column and the
    resulting token-count matrix is forwarded to the wrapped classifier's
    ``train`` method. During inference the already-fitted vectorizer transforms
    the text before calling the classifier's ``predict`` method.

    References
    ----------
    - [1] https://scikit-learn.org/stable/modules/generated/sklearn.feature_extraction.text.CountVectorizer.html
    """

    DISPLAY_NAME: str = MultilingualString(
        en="Bag of Words Text Classifier",
        es="Clasificador de Texto Bolsa de Palabras",
        pt="Classificador de Texto BOW",
        de="Bag-of-Words-Textklassifikator",
        zh="词袋文本分类器",
    )
    DESCRIPTION: str = MultilingualString(
        en="Text classification using bag-of-words features and tabular classifiers.",
        es=(
            "Clasificación de texto usando bolsa de palabras y "
            "clasificadores tabulares."
        ),
        pt=(
            "Classificação de texto usando características de BOW e "
            "classificadores tabulares."
        ),
        de=(
            "Textklassifikation mit Bag-of-Words-Merkmalen und tabellarischen "
            "Klassifikatoren."
        ),
        zh="使用词袋特征和表格分类器进行文本分类。",
    )
    COLOR: str = "#FF5722"
    ICON: str = "TextFields"
    SCHEMA = BagOfWordsTextClassificationModelSchema

    def __init__(self, **kwargs) -> None:
        """Initialise the Bag-of-Words text classification meta-model.

        Creates a ``CountVectorizer`` with the configured n-gram range and
        stores the preinstantiated tabular classifier that will be trained on
        the resulting token-count matrix.

        Parameters
        ----------
        **kwargs : dict
            tabular_classifier : TabularClassificationModel
                An already-instantiated DashAI tabular classifier to use as
                the underlying prediction model.
            ngram_min_n : int
                Minimum n-gram size for the ``CountVectorizer`` (≥ 1).
            ngram_max_n : int
                Maximum n-gram size for the ``CountVectorizer`` (≥ 1).
        """

        # Lazy import of CountVectorizer
        from sklearn.feature_extraction.text import CountVectorizer

        self.classifier = kwargs["tabular_classifier"]
        self.vectorizer = CountVectorizer(
            ngram_range=(kwargs["ngram_min_n"], kwargs["ngram_max_n"])
        )

    def get_vectorizer(self, input_column: str, output_column: Optional[str] = None):
        """Factory that returns a function to transform a text classification dataset
        into a tabular classification dataset.

        To do this, the column "text" is vectorized (using a BagOfWords) into a sparse
        matrix of size NxM, where N is the number of examples and M is the vocabulary
        size.

        Each column of the output matrix will be named using the input_column name as
        prefix and the column number as suffix.

        The output_column is not changed.

        Parameters
        ----------
        input_column : str
            name the input column of the dataset. This column will be vectorized.

        output_column : str
            name the output column of the dataset.

        Returns
        -------
        Function
            Function for vectorize the dataset.
        """

        def _vectorize(example) -> dict:
            """Vectorize a single dataset example using the fitted CountVectorizer.

            Parameters
            ----------
            example : dict
                A single dataset row.  Must contain the key ``input_column``
                whose value is the raw text string to transform.

            Returns
            -------
            dict
                A flat dictionary mapping ``input_column + str(idx)`` to the
                corresponding token count for each vocabulary index ``idx``.
            """
            # Lazy import of numpy
            import numpy as np

            vectorized_sentence = self.vectorizer.transform(
                [example[input_column]]
            ).toarray()
            output_example = {}
            for idx in range(np.shape(vectorized_sentence)[1]):
                output_example[input_column + str(idx)] = vectorized_sentence[0][idx]
            return output_example

        return _vectorize

    def train(
        self,
        x,
        y,
        x_validation=None,
        y_validation=None,
    ):
        """Fit the bag-of-words vectorizer and the underlying tabular classifier.

        The text column is first vectorized with the fitted ``CountVectorizer``
        to produce a token-count matrix, which is then passed to the wrapped
        tabular classifier for training.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset containing the raw text column.
        y : DashAIDataset
            Target dataset containing the class labels.
        x_validation : DashAIDataset or None, optional
            Validation inputs.  Not used by the default tabular classifiers
            but accepted for interface compatibility.
        y_validation : DashAIDataset or None, optional
            Validation targets.  Not used by the default tabular classifiers
            but accepted for interface compatibility.
        """
        input_column = x.column_names[0]
        self.vectorizer.fit(x[input_column])
        tokenizer_func = self.get_vectorizer(input_column)
        tokenized_dataset = x.map(tokenizer_func, remove_columns=x.column_names)
        # Lazy import of converter
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        tokenized_dataset = to_dashai_dataset(tokenized_dataset)

        self.classifier.train(tokenized_dataset, y)

    def predict(self, x):
        """Generate class-probability predictions for the input text dataset.

        The raw text column is transformed using the already-fitted
        ``CountVectorizer``, and the resulting token-count matrix is forwarded
        to the wrapped tabular classifier's ``predict`` method.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset containing the raw text column.

        Returns
        -------
        numpy.ndarray
            Array of shape ``(n_samples, n_classes)`` with predicted
            probabilities for each class, as returned by the wrapped
            tabular classifier.
        """
        input_column = x.column_names[0]

        tokenizer_func = self.get_vectorizer(input_column)
        tokenized_dataset = x.map(tokenizer_func, remove_columns=x.column_names)
        # Lazy import of converter
        from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

        tokenized_dataset = to_dashai_dataset(tokenized_dataset)

        return self.classifier.predict(tokenized_dataset)

    def save(self, filename: Union[str, "Path"]) -> None:
        """Serialise the model to disk using joblib.

        Parameters
        ----------
        filename : str or Path
            Destination file path where the model will be written.
        """
        # Lazy import of joblib
        import joblib

        joblib.dump(self, filename)

    @staticmethod
    def load(filename: Union[str, "Path"]) -> None:
        """Deserialise a model from disk using joblib.

        Parameters
        ----------
        filename : str or Path
            Path to the file previously written by :meth:`save`.

        Returns
        -------
        BagOfWordsTextClassificationModel
            The loaded model instance.
        """
        # Lazy import of joblib
        import joblib

        model = joblib.load(filename)
        return model

    def prepare_dataset(self, dataset: "DashAIDataset", is_fit=False):
        """Apply the model transformations to the dataset.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to be transformed.
        is_fit : bool, optional
            If True, the method will apply transformations needed for fitting the model.

        Returns
        -------
        DashAIDataset
            The prepared dataset ready to be converted to
            an accepted format in the model.
        """
        try:
            input_column = dataset.column_names[0]
            input_type = dataset.types[input_column]

            if isinstance(input_type, Categorical):
                if is_fit:
                    dataset = super().prepare_dataset(dataset, is_fit=True)
                    return dataset
                else:
                    dataset = super().prepare_dataset(dataset, is_fit=False)
                    return dataset

            if is_fit:
                self.vectorizer.fit(dataset[input_column])

            tokenizer_func = self.get_vectorizer(input_column)
            dataset = dataset.map(tokenizer_func, remove_columns=input_column)
            # Lazy import converters and pyarrow
            import pyarrow as pa

            from DashAI.back.dataloaders.classes.dashai_dataset import to_dashai_dataset

            dataset = to_dashai_dataset(dataset)

            dataset.types = {
                col: Float(arrow_type=pa.float32())
                for col in dataset.column_names
                if col.startswith(input_column)
            }

            return dataset
        except Exception as e:
            print(f"Couldn't apply transformations to the dataset for the model: {e}")

    def prepare_output(self, dataset, is_fit=False):
        """Prepare output targets by delegating to the wrapped classifier.

        Passes the output dataset directly to the underlying tabular
        classifier's ``prepare_output`` method, which applies label encoding
        as required by the classifier.

        Parameters
        ----------
        dataset : DashAIDataset
            The output dataset containing the target labels to be prepared.
        is_fit : bool, optional
            If ``True``, fit the label encoder on the dataset before
            transforming.  If ``False``, apply existing encodings.
            Default is ``False``.

        Returns
        -------
        DashAIDataset
            The prepared output dataset with categorical labels encoded as
            integers.
        """
        return self.classifier.prepare_output(dataset, is_fit)
