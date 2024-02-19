import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from DashAI.back.core.schema_fields import BaseSchema, component_field, int_field
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.text_classification_model import TextClassificationModel


class NumericalWrapperForTextSchema(BaseSchema):
    """
    NumericalWrapperForText is a metamodel that allows text classification using
    tabular classifiers and a tokenizer.
    """

    tabular_classifier: component_field(
        description="Tabular model used as the underlying model"
        "to generate the text classifier.",
        parent="TabularClassificationModel",
    )
    ngram_min_n: int_field(
        description="Minimum n_gram to use in the vectorizer.",
        default=1,
        ge=1,
    )
    ngram_max_n: int_field(
        description="Maximum n_gram to use in the vectorizer.",
        default=1,
        le=1,
    )


class NumericalWrapperForText(TextClassificationModel, SklearnLikeModel):
    """Text classification meta-model."""

    SCHEMA = NumericalWrapperForTextSchema

    def __init__(self, **kwargs) -> None:
        kwargs = self.validate_and_transform(kwargs)
        self.classifier = kwargs["tabular_classifier"]
        self.vectorizer = CountVectorizer(
            ngram_range=(kwargs["ngram_min_n"], kwargs["ngram_max_n"])
        )

    def get_vectorizer(self, input_column: str, output_column: str):
        """Vectorize input.
        The vectorized input is assumed to be an array of numbers,
        so each number is placed in the input_label_idx column,
        with idx being the position of the number in the array.

        Parameters
        ----------
        input_column : str
            name the input column to be vectorized.
        output_column : str
            name the output column to be vectorized.

        Returns
        -------
        Function
            Function for vectorization of the dataset.
        """

        def _vectorize(example) -> dict:
            vectorized_sentence = self.vectorizer.transform(
                [example[input_column]]
            ).toarray()
            output_example = {}
            for idx in range(np.shape(vectorized_sentence)[1]):
                output_example[input_column + str(idx)] = vectorized_sentence[0][idx]
            output_example[output_column] = example[output_column]
            return output_example

        return _vectorize

    def fit(self, dataset: DashAIDataset):
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        self.vectorizer.fit(dataset[input_column])
        out_input_columns = [
            input_column + str(idx) for idx in range(len(self.vectorizer.vocabulary_))
        ]

        tokenizer_func = self.get_vectorizer(input_column, output_column)
        dataset = dataset.map(tokenizer_func, remove_columns="text")
        self.classifier.fit(
            DashAIDataset(dataset.data, out_input_columns, [output_column])
        )

    def predict(self, dataset: DashAIDataset):
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        out_input_columns = [
            input_column + str(idx) for idx in range(len(self.vectorizer.vocabulary_))
        ]

        tokenizer_func = self.get_vectorizer(input_column, output_column)
        dataset = dataset.map(tokenizer_func, remove_columns="text")
        return self.classifier.predict(
            DashAIDataset(dataset.data, out_input_columns, [output_column])
        )
