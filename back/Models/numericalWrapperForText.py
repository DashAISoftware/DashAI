import json
from sklearn.feature_extraction.text import CountVectorizer
#from sklearnLikeModel import SkleanLikeModel
from model import Model


#class NumericalWrapperForText(SkleanLikeModel, TextClassificationModel):
class NumericalWrapperForText(Model):
    """
    Wrapper for TextClassificationTask that uses a numericClassificationModel 
    to classify text, it uses a simple bag of words model to vectorize the 
    text and give it to the numerical model to perform the prediction.
    """

    MODEL = "numericalwrapperfortext"
    with open(f"Models/parameters/models_schemas/{MODEL}.json") as f:
        SCHEMA = json.load(f)

    def __init__(self, **kwargs) -> None:
        ngram_min_n = kwargs.pop("ngram_min_n")
        ngram_max_n = kwargs.pop("ngram_max_n")
        kwargs["n_gram"] = (ngram_min_n,ngram_max_n)
        self.classifier = kwargs.pop("numeric_classifier")
        self.vectorizer = CountVectorizer(**kwargs)

    def fit(self, x, y):
        self.classifier.fit(self.vectorizer.fit_transform(x), y)

    def predict(self, x):
        return self.classifier.predict(self.vectorizer.fit_transform(x))
