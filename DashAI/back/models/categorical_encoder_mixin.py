"""Shared categorical-encoding behavior for tabular DashAI models.

Models that feed tabular data into an estimator (scikit-learn wrappers, the
PyTorch MLP, etc.) need their ``Categorical`` feature columns turned into a
numeric representation before training/prediction. This mixin centralises that
logic so each model does not reimplement it.

The mixin provides the ``prepare_dataset`` / ``prepare_output`` hooks expected
by ``BaseModel`` and the fitted encoder state. Persistence of that state is left
to each concrete model (``SklearnLikeModel`` pickles the whole instance via
joblib; the MLP serialises the fields explicitly through ``torch.save``).
"""

from typing import TYPE_CHECKING, Any, List, Optional

if TYPE_CHECKING:
    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


class CategoricalEncoderMixin:
    """Encode ``Categorical`` feature/target columns into numeric columns.

    When fitting, columns whose ``encoder`` preference is ``"label"`` are label
    encoded; every other categorical column is one-hot encoded (the safe default,
    since one hot introduces no false ordinal relationship). When applying (not
    fitting), the encoders that were actually fitted are applied based on the
    stored state (``encodings`` / ``one_hot_encoder``) rather than the dataset's
    current ``encoder`` metadata, which can drift between training and prediction
    (e.g. a round-trip through Arrow metadata resets the preference to its
    default).
    """

    def _setup_categorical_encoders(self) -> None:
        """Initialise the fitted-encoder state.

        Concrete models must call this from their ``__init__`` (and ensure the
        fields are persisted by their ``save`` / restored by their ``load``).
        """
        self.encodings: dict = {}
        self.one_hot_encoder: Optional[Any] = None
        self.categorical_columns: List[str] = []
        self.output_encodings: dict = {}

    def prepare_dataset(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Encode categorical feature columns into a numeric representation.

        Parameters
        ----------
        dataset : DashAIDataset
            The input dataset to preprocess.
        is_fit : bool
            If True, fit the encoders on the data. If False, apply previously
            fitted encoders. Defaults to False.

        Returns
        -------
        DashAIDataset
            The dataset with categorical columns converted to numeric columns.
        """
        from DashAI.back.types.categorical import Categorical

        if not is_fit:
            # Apply exactly the encoders fitted during training, regardless of
            # the dataset's (possibly drifted) per column encoder preference.
            prepared = dataset
            if self.encodings:
                prepared = self._prepare_label_encoded(
                    prepared, is_fit, columns=list(self.encodings.keys())
                )
            if self.one_hot_encoder is not None:
                prepared = self._prepare_one_hot(
                    prepared, is_fit, columns=self.categorical_columns
                )
            return prepared

        types = dataset.types
        if not any(isinstance(t, Categorical) for t in types.values()):
            return dataset

        label_cols = [
            c
            for c, t in types.items()
            if isinstance(t, Categorical) and t.encoder == "label"
        ]
        # Everything categorical that is not explicitly label-encoded is one-hot
        # encoded (the safe default: no false ordinal relationship).
        one_hot_cols = [
            c
            for c, t in types.items()
            if isinstance(t, Categorical) and t.encoder != "label"
        ]

        prepared = dataset
        if label_cols:
            prepared = self._prepare_label_encoded(prepared, is_fit, columns=label_cols)
        if one_hot_cols:
            prepared = self._prepare_one_hot(prepared, is_fit, columns=one_hot_cols)
        return prepared

    def prepare_output(
        self, dataset: "DashAIDataset", is_fit: bool = False
    ) -> "DashAIDataset":
        """Prepare output targets using label encoding.

        Parameters
        ----------
        dataset : DashAIDataset
            The output dataset to be transformed.
        is_fit : bool, optional
            If True, fit the encoder. If False, use existing encodings.

        Returns
        -------
        DashAIDataset
            Dataset with categorical columns converted to integers.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset_utils import (
            apply_categorical_label_encoder,
            categorical_label_encoder,
        )

        prepared = dataset
        if is_fit:
            prepared, encodings = categorical_label_encoder(dataset)
            self.output_encodings.update(encodings)
        elif self.output_encodings:
            prepared = apply_categorical_label_encoder(dataset, self.output_encodings)
        return prepared

    def _prepare_label_encoded(
        self, dataset: "DashAIDataset", is_fit: bool, columns: list = None
    ) -> "DashAIDataset":
        """Prepare dataset using label encoding for categorical columns.

        This is appropriate for tree based models that don't assume
        ordinal relationships between encoded values.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to be transformed.
        is_fit : bool
            If True, fit the encoder. If False, use existing encodings.
        columns : list, optional
            If given, only label-encode the specified columns.

        Returns
        -------
        DashAIDataset
            Dataset with categorical columns converted to integers.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset_utils import (
            apply_categorical_label_encoder,
            categorical_label_encoder,
        )

        prepared = dataset
        if is_fit:
            prepared, encodings = categorical_label_encoder(dataset, columns=columns)
            self.encodings.update(encodings)
        elif self.encodings:
            relevant_encodings = {
                k: v
                for k, v in self.encodings.items()
                if columns is None or k in columns
            }
            prepared = apply_categorical_label_encoder(dataset, relevant_encodings)
        return prepared

    def _prepare_one_hot(
        self, dataset: "DashAIDataset", is_fit: bool, columns: list = None
    ) -> "DashAIDataset":
        """Prepare dataset using one hot encoding for categorical columns.

        Parameters
        ----------
        dataset : DashAIDataset
            The dataset to be transformed.
        is_fit : bool
            If True, fit the encoder. If False, use existing encoder.
        columns : list, optional
            If given, only one hot encode the specified columns.

        Returns
        -------
        DashAIDataset
            Dataset with categorical columns replaced by one hot columns.
        """
        from DashAI.back.dataloaders.classes.dashai_dataset_utils import (
            apply_categorical_one_hot_encoder,
            categorical_one_hot_encoder,
        )

        if is_fit:
            prepared, encoder, cat_cols = categorical_one_hot_encoder(
                dataset, columns=columns
            )
            self.one_hot_encoder = encoder
            self.categorical_columns = cat_cols
        elif self.one_hot_encoder is not None:
            prepared = apply_categorical_one_hot_encoder(
                dataset, self.one_hot_encoder, self.categorical_columns
            )
        else:
            prepared = dataset
        return prepared
