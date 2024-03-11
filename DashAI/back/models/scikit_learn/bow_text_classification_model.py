from typing import List

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from DashAI.back.core.schema_fields import BaseSchema, component_field, int_field
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.scikit_learn.sklearn_like_model import SklearnLikeModel
from DashAI.back.models.text_classification_model import TextClassificationModel


class BagOfWordsTextClassificationModelSchema(BaseSchema):
    """
    NumericalWrapperForText is a metamodel that allows text classification using
    tabular classifiers and a tokenizer.
    """

    tabular_classifier: component_field(
        description=(
            "Tabular model used as the underlying model "
            "to generate the text classifier."
        ),
        parent="TabularClassificationModel",
    )  # type: ignore
    ngram_min_n: int_field(
        description=(
            "The lower boundary of the range of n-values for different word n-grams "
            "or char n-grams to be extracted. It must be an integer greater or equal "
            "than 1"
        ),
        placeholder=1,
        ge=1,
    )  # type: ignore
    ngram_max_n: int_field(
        description=(
            "The upper boundary of the range of n-values for different word n-grams "
            "or char n-grams to be extracted. It must be an integer greater or equal "
            "than 1"
        ),
        placeholder=1,
        ge=1,
    )  # type: ignore


class BagOfWordsTextClassificationModel(TextClassificationModel, SklearnLikeModel):
    """Text classification meta-model.

    The metamodel has two main components:
    - Tabular classification model, the underlying model that processes the data and
      provides the prediction.
    - Vectorizer, a BagOfWords that vectorizes the text into a sparse matrix to give
      the correct input to the underlying model.

    The tabular_model and vecotorizer are created in the __init__ method and stored in
    the model.

    To train the tabular_model the vectorizer is fitted and used to transform the
    train dataset.

    To predict with the tabular_model the vectorizer is used to transform the dataset.
    """

    SCHEMA = BagOfWordsTextClassificationModelSchema

    def __init__(self, **kwargs) -> None:
        self.classifier = kwargs["tabular_classifier"]
        self.vectorizer = CountVectorizer(
            ngram_range=(kwargs["ngram_min_n"], kwargs["ngram_max_n"])
        )

    def get_vectorizer(self, input_column: str, output_column: str):
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
            vectorized_sentence = self.vectorizer.transform(
                [example[input_column]]
            ).toarray()
            output_example = {}
            for idx in range(np.shape(vectorized_sentence)[1]):
                output_example[input_column + str(idx)] = vectorized_sentence[0][idx]
            output_example[output_column] = example[output_column]
            return output_example

        return _vectorize

    def vocab_cols(self, input_column: str) -> List[str]:
        """Names of the columns of the tokenized dataset.

        When the dataset is vectorized, the "text" column is transformed into several
        columns to represent a sparse matrix.

        This function returns the names of each column of the new dataset.

        The output list will have M names, where M is the size of the vocabulary.

        Before calling this function it is necessary that the vectorizer is set.

        Parameters
        ----------
        input_column : str
            name the input column of the original dataset.

        Returns
        -------
        List[str]
            List with the column names of the tokenized dataset.
        """
        return [
            input_column + str(idx) for idx in range(len(self.vectorizer.vocabulary_))
        ]

    def fit(self, dataset: DashAIDataset):
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        self.vectorizer.fit(dataset[input_column])
        tokenizer_func = self.get_vectorizer(input_column, output_column)
        tokenized_dataset = dataset.map(tokenizer_func, remove_columns="text")

        vocab_cols = self.vocab_cols(input_column)

        self.classifier.fit(
            DashAIDataset(tokenized_dataset.data, vocab_cols, [output_column])
        )

    def predict(self, dataset: DashAIDataset):
        input_column = dataset.inputs_columns[0]
        output_column = dataset.outputs_columns[0]

        tokenizer_func = self.get_vectorizer(input_column, output_column)
        tokenized_dataset = dataset.map(tokenizer_func, remove_columns="text")

        vocab_cols = self.vocab_cols(input_column)

        return self.classifier.predict(
            DashAIDataset(tokenized_dataset.data, vocab_cols, [output_column])
        )
