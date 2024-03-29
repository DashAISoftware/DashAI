import json

from sklearn.feature_extraction.text import CountVectorizer

from DashAI.back.models import SklearnLikeModel
from DashAI.back.models.text_classification_model import TextClassificationModel


class NumericalWrapperForText(TextClassificationModel, SklearnLikeModel):
    """Text classification metamodel."""

    MODEL = "numericalwrapperfortext"
    with open(f"DashAI/back/models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self, **kwargs) -> None:
        ngram_min_n = kwargs.pop("ngram_min_n")
        ngram_max_n = kwargs.pop("ngram_max_n")
        kwargs["ngram_range"] = (ngram_min_n, ngram_max_n)
        self.classifier = kwargs.pop("numeric_classifier")
        self.vectorizer = CountVectorizer(**kwargs)

    def fit(self, x, y):
        self.classifier.fit(self.vectorizer.fit_transform(x), y)

    def predict(self, x):
        return self.classifier.predict(self.vectorizer.transform(x))

    def score(self, x, y):
        return self.classifier.score(self.vectorizer.transform(x), y)

    def get_params(self):
        ngram_min, ngram_max = self.vectorizer.get_params()["ngram_range"]
        params_dict = {
            "numeric_classifier": {
                "choice": self.classifier.MODEL,
                **self.classifier.get_params(),
            },
            "ngram_min_n": ngram_min,
            "ngram_max_n": ngram_max,
        }
        return params_dict
