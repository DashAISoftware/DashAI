from typing import Any

from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset
from DashAI.back.models.text_classification_model import TextClassificationModel


class DummyTextClassifier(TextClassificationModel):
    """Dummy model for text classification.

    Implements a simple classifier that predicts the majority class
    of a binary classification problem.
    """

    def __init__(self, strategy: str = "most_frequent"):
        """
        Parameters
        ----------
        strategy : str, optional
            Strategy for predictions:
            - 'most_frequent': Always predicts the most common class in the dataset.
        """
        super().__init__()
        self.strategy = strategy
        self.most_frequent_label = None
        self.is_trained = False

    def tokenize_data(self, dataset: DashAIDataset) -> DashAIDataset:
        """Tokenize the input dataset.

        This dummy implementation is a no-op that returns the dataset unchanged.
        It exists solely to satisfy the ``TextClassificationModel`` interface.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to tokenize.

        Returns
        -------
        DashAIDataset
            The dataset, unmodified.
        """
        return dataset

    def fit(self, x_train: DashAIDataset, y_train: DashAIDataset) -> None:
        """Fit the dummy classifier by computing its prediction strategy.

        For the ``"most_frequent"`` strategy, determines the majority class
        label from ``y_train`` and stores it for use in :meth:`predict`.

        Parameters
        ----------
        x_train : DashAIDataset
            Training features. Not used by the dummy classifier.
        y_train : DashAIDataset
            Training labels. The first column is used to find the majority
            class when ``strategy="most_frequent"``.
        """
        if self.strategy == "most_frequent":
            column_name = y_train.column_names[0]
            labels = y_train[column_name]
            self.most_frequent_label = max(set(labels), key=labels.count)
        self.is_trained = True

    def predict(self, x_pred: DashAIDataset) -> DashAIDataset:
        """Predict labels for every row in the input dataset.

        Parameters
        ----------
        x_pred : DashAIDataset
            Input features. The number of rows determines the number of
            predictions returned.

        Returns
        -------
        DashAIDataset
            Dataset with a single column ``"predictions"`` containing one
            predicted label per row.

        Raises
        ------
        RuntimeError
            If :meth:`fit` has not been called yet.
        ValueError
            If the configured ``strategy`` is unknown.
        """
        from datasets import Dataset

        if not self.is_trained:
            raise RuntimeError("The model must be trained before making predictions.")

        if self.strategy == "most_frequent":
            predictions = [self.most_frequent_label] * len(x_pred)
        else:
            raise ValueError(f"Unknown strategy: {self.strategy}")

        return Dataset.from_dict({"predictions": predictions})

    def save(self, filename: str) -> None:
        """Persist the model state to a plain-text file.

        Writes the prediction strategy and the most-frequent label to
        ``filename``, one value per line, so the model can be restored later
        with :meth:`load`.

        Parameters
        ----------
        filename : str
            Path to the file where the model state will be written.
        """
        with open(filename, "w") as f:
            f.write(f"{self.strategy}\n")
            f.write(f"{self.most_frequent_label}\n")

    def load(self, filename: str) -> Any:
        """Restore the model state from a plain-text file.

        Reads the prediction strategy and the most-frequent label from
        ``filename`` (as written by :meth:`save`) and marks the model as
        trained.

        Parameters
        ----------
        filename : str
            Path to the file from which the model state will be read.

        Returns
        -------
        Any
            ``None``.  The model state is updated in place; the return value
            is not used by the base class interface.
        """
        with open(filename, "r") as f:
            self.strategy = f.readline().strip()
            self.most_frequent_label = f.readline().strip()
        self.is_trained = True

    def prepare_dataset(self, dataset, is_fit=False):
        """Prepare the dataset for training or inference.

        This dummy implementation is a no-op that returns the dataset
        unchanged.  It exists to satisfy the ``TextClassificationModel``
        interface without applying any transformations.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to prepare.
        is_fit : bool, optional
            If ``True``, the preparation is for fitting (training).  Ignored
            by this implementation.  Default is ``False``.

        Returns
        -------
        DashAIDataset
            The dataset, unmodified.
        """
        return dataset
