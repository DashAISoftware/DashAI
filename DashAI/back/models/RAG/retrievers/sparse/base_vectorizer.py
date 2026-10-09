from typing import Final

from DashAI.back.config_object import ConfigObject


class BaseVectorizer(ConfigObject):
    """Base class for the vectorizers configured inside sparse retrievers.

    A vectorizer only builds the configured scikit-learn vectorizer. The
    sparse retriever that owns it fits it on the chunks and persists it.
    """

    TYPE: Final[str] = "Vectorizer"
