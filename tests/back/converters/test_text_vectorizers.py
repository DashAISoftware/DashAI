"""TF-IDF and bag of words share the RAG vectorizer options."""

import pyarrow as pa
import pytest
from pydantic import ValidationError
from sklearn.feature_extraction.text import ENGLISH_STOP_WORDS

from DashAI.back.converters.scikit_learn.bag_of_words import BagOfWordsConverter
from DashAI.back.converters.scikit_learn.tf_idf import TFIDFConverter
from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.types.value_types import Text

TEXTS = ["the cat sat", "the dog ran", "a cat and a dog"]

BASE_PARAMS = {
    "max_features": None,
    "lowercase": True,
    "strip_accents": None,
    "analyzer": "word",
    "stop_words": None,
    "custom_stop_words": None,
    "lower_bound_ngrams": 1,
    "upper_bound_ngrams": 1,
    "min_df": 0.0,
    "max_df": 1.0,
}
TFIDF_PARAMS = {
    **BASE_PARAMS,
    "norm": "l2",
    "use_idf": True,
    "smooth_idf": True,
    "sublinear_tf": False,
}


def _dataset():
    return DashAIDataset(
        pa.table({"text": pa.array(TEXTS, type=pa.string())}),
        types={"text": Text(arrow_type=pa.string())},
    )


def test_fit_matrix_and_transform_matrix_agree():
    converter = BagOfWordsConverter(**BASE_PARAMS)

    fitted = converter.fit_matrix(TEXTS)
    again = converter.transform_matrix(TEXTS)

    assert fitted.shape == again.shape == (3, len(converter.vectorizer.vocabulary_))
    assert (fitted != again).nnz == 0


def test_transform_matrix_needs_a_fit():
    with pytest.raises(RuntimeError, match="fitted"):
        TFIDFConverter(**TFIDF_PARAMS).transform_matrix(TEXTS)


def test_the_rag_options_reach_scikit_learn():
    converter = TFIDFConverter(
        **{
            **TFIDF_PARAMS,
            "strip_accents": "unicode",
            "analyzer": "char_wb",
            "norm": None,
            "sublinear_tf": True,
            "max_df": 0.9,
        }
    )

    options = converter.vectorizer.get_params()
    assert options["strip_accents"] == "unicode"
    assert options["analyzer"] == "char_wb"
    assert options["norm"] is None
    assert options["sublinear_tf"] is True
    assert options["max_df"] == 0.9
    assert options["max_features"] is None


def test_english_and_custom_stop_words_are_merged():
    converter = BagOfWordsConverter(
        **{**BASE_PARAMS, "stop_words": "english", "custom_stop_words": ["cat"]}
    )

    words = set(converter.vectorizer.get_params()["stop_words"])
    assert "cat" in words
    assert set(ENGLISH_STOP_WORDS) <= words


def test_notebook_columns_keep_their_names_and_types():
    data = _dataset()

    tfidf = TFIDFConverter(**TFIDF_PARAMS).fit(data).transform(data)
    bow = BagOfWordsConverter(**BASE_PARAMS).fit(data).transform(data)

    assert "text" in tfidf.column_names
    assert "tfidf_cat" in tfidf.column_names
    assert tfidf.arrow_table.column("tfidf_cat").type == pa.float64()
    assert bow.arrow_table.column("bow_cat").type == pa.int64()
    assert bow.arrow_table.column("bow_cat").to_pylist() == [1, 0, 1]


@pytest.mark.parametrize(
    ("converter", "params"),
    [(TFIDFConverter, TFIDF_PARAMS), (BagOfWordsConverter, BASE_PARAMS)],
)
def test_document_frequency_bounds_must_be_ordered(converter, params):
    with pytest.raises(ValidationError):
        converter.SCHEMA.model_validate({**params, "min_df": 0.8, "max_df": 0.2})
    converter.SCHEMA.model_validate({**params, "min_df": 0.5, "max_df": 0.5})
