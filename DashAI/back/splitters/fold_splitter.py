from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Dict, List, Tuple

from DashAI.back.dataloaders.classes.dashai_dataset import split_dataset_cv

from .base_splitter import BaseSplitter

if TYPE_CHECKING:
    from datasets import DatasetDict

    from DashAI.back.dataloaders.classes.dashai_dataset import DashAIDataset


def sklearn_random_state(shuffle: bool, random_state: int):
    """Adapt a seed to scikit-learn's shuffle contract.

    The ``KFold`` family raises when ``random_state`` is set while ``shuffle``
    is False, so the seed is only forwarded when it can have an effect. Meant
    for the splitters that expose ``shuffle`` as a parameter; the repeated
    splitters always shuffle and take no such argument, so they pass their seed
    through directly.

    Parameters
    ----------
    shuffle : bool
        Whether the splitter shuffles before splitting.
    random_state : int
        The configured seed.

    Returns
    -------
    int or None
        ``random_state`` when shuffling, ``None`` otherwise.
    """
    return random_state if shuffle else None


class FoldSplitter(BaseSplitter):
    """Shared base class for splitters that generate multiple cross-validation folds.

    This abstraction centralizes the logic required by fold-based evaluation
    strategies: it reserves an optional test set, builds several
    train/validation partitions over the rows that are left, and adds a final
    partition that fits the model on all of them and scores it on the reserved
    ones.
    """

    # Every fold splitter produces several train and validation pairs rather
    # than one set of partitions, which is what pairs it with the
    # cross-validation strategy instead of the holdout one.
    PARTITIONING: str = "folds"

    # How the rows of the test set are chosen. ``"random"`` samples them
    # uniformly, ``"stratified"`` preserves the target distribution, and
    # ``"group"`` moves whole groups so a group never spans the carve.
    TEST_SPLIT_STRATEGY: str = "random"

    @classmethod
    def explainable_partitions(cls, split_indexes):
        """Return the partitions of a fold based run an explainer may target.

        The folds themselves are not offered: the model that gets saved is refit
        on everything the folds could use, so only the reserved rows are data it
        has not seen. Those are the same rows the run reports its test metrics
        on, which is why they carry the ``test`` name here too.

        Parameters
        ----------
        split_indexes : dict
            The ``Run.split_indexes`` payload, already parsed.

        Returns
        -------
        dict
            Row indexes for the ``train`` and ``test`` partitions.
        """
        full_dataset = split_indexes["full_dataset"]
        return {
            "train": full_dataset["train_indexes"],
            "test": full_dataset.get("test_indexes", []),
        }

    def __init__(self, splits_data):
        """Initialize the fold splitter with the requested number of splits.

        Parameters
        ----------
        splits_data : dict
            Configuration dictionary that may include the number of folds to
            generate and the proportion of the dataset to reserve as a test
            set.
        """
        super().__init__(splits_data)
        self.n_splits = splits_data.get("n_splits", 5)
        # Sessions created before the test set existed name no proportion, and
        # reserving rows for them would silently shrink the folds of a session
        # whose earlier runs used every row. The schema placeholder gives new
        # sessions their 0.1, so only the older ones land on this default.
        self.test_size = splits_data.get("test_size", 0)

    @classmethod
    def get_metadata(cls) -> dict:
        """Return metadata describing the splitter's compatibility."""
        return {
            **super().get_metadata(),
            "compatibleInnerSplitters": getattr(cls, "COMPATIBLE_INNER_SPLITTERS", []),
        }

    @abstractmethod
    def split_indexes(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> List[Tuple[List, List]]:
        """Generate train/test index pairs for each fold.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset to be partitioned.
        y : DashAIDataset
            Target values associated with ``x``.

        Returns
        -------
        list[tuple]
            A list of train/test index pairs for every fold.
        """
        raise NotImplementedError(
            "The split indexes method must be implemented by subclasses."
        )

    def _carve_test_split(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> Tuple[List[int], List[int]]:
        """Reserve the rows that stay out of cross-validation.

        The reserved rows are picked according to ``TEST_SPLIT_STRATEGY`` so the
        carve respects whatever the splitter guarantees: a stratified splitter
        keeps the class balance, and a grouped one never splits a group.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset being split.
        y : DashAIDataset
            Target values associated with ``x``.

        Returns
        -------
        tuple[list[int], list[int]]
            The test row indexes and the rows left for the folds, both as
            positions in the original dataset.

        Raises
        ------
        ValueError
            If the requested proportion leaves no rows on either side.
        """
        import numpy as np

        all_indexes = list(range(len(x)))
        if not self.test_size:
            return [], all_indexes

        n_test = int(round(len(x) * self.test_size))
        if n_test < 1 or len(x) - n_test < self.n_splits:
            raise ValueError(
                f"""A test set of {self.test_size} leaves too few rows: it
                would reserve {n_test} of {len(x)} samples and leave
                {len(x) - n_test} for {self.n_splits} folds."""
            )

        indexes = np.arange(len(x))
        seed = self.random_state

        if self.TEST_SPLIT_STRATEGY == "temporal":
            # The reserved rows must be the most recent ones. Every other
            # strategy samples them from anywhere in the dataset, which for a
            # series would scatter future rows through the training data of
            # every fold and report a score that cannot be reproduced in use.
            return (
                [int(i) for i in indexes[-n_test:]],
                [int(i) for i in indexes[:-n_test]],
            )

        if self.TEST_SPLIT_STRATEGY == "group":
            from sklearn.model_selection import GroupShuffleSplit

            groups = x.to_pandas()[self.group_column]
            splitter = GroupShuffleSplit(
                n_splits=1, test_size=self.test_size, random_state=seed
            )
            pool, test_rows = next(splitter.split(indexes, groups=groups))
        elif self.TEST_SPLIT_STRATEGY == "stratified":
            from sklearn.model_selection import StratifiedShuffleSplit

            splitter = StratifiedShuffleSplit(
                n_splits=1, test_size=self.test_size, random_state=seed
            )
            pool, test_rows = next(splitter.split(indexes, y=self.prepare_y(y)))
        else:
            from sklearn.model_selection import ShuffleSplit

            splitter = ShuffleSplit(
                n_splits=1, test_size=self.test_size, random_state=seed
            )
            pool, test_rows = next(splitter.split(indexes))

        return sorted(int(i) for i in test_rows), sorted(int(i) for i in pool)

    def split(
        self, x: DashAIDataset, y: DashAIDataset
    ) -> Tuple[List[DatasetDict], List[DatasetDict], Dict[str, Any]]:
        """Create folds and return both the partitioned datasets and the indices.

        Parameters
        ----------
        x : DashAIDataset
            Input dataset to split.
        y : DashAIDataset
            Target values associated with ``x``.

        Returns
        -------
        tuple[list, list, dict]
            A tuple containing the split datasets for every fold and a mapping
            from fold names to their corresponding train/test indices.

        Raises
        ------
        ValueError
            If the number of samples is lower than the number of requested
            splits.
        """
        test_indexes, fold_pool = self._carve_test_split(x, y)

        if len(fold_pool) < self.n_splits:
            raise ValueError(f"""Number of splits (n_splits={self.n_splits}) cannot be
                greater than the number of samples ({len(fold_pool)}).""")

        # The folds are built over the rows left after the carve, so
        # ``split_indexes`` sees a dataset without the reserved rows and returns
        # positions within it, which are mapped back to original row numbers.
        # ``fold_pool`` is sorted, so filtering the reserved rows out keeps the
        # rows in the order the mapping below assumes.
        pool_x = split_dataset_cv(x, fold_pool, [])["train"] if test_indexes else x
        pool_y = split_dataset_cv(y, fold_pool, [])["train"] if test_indexes else y
        folds = self.split_indexes(pool_x, pool_y)

        indices = {}
        x_prepared, y_prepared = [], []

        # A fold is scored on the rows it held back from its own training, which
        # is a validation estimate: the reserved rows below are the only data no
        # fold and no hyperparameter search ever touched.
        for i, (train_positions, validation_positions) in enumerate(folds):
            train_idx = [fold_pool[p] for p in train_positions]
            validation_idx = [fold_pool[p] for p in validation_positions]
            indice = {
                "train_indexes": train_idx,
                "validation_indexes": validation_idx,
            }
            indices[f"fold_{i}"] = indice

            x_prepared.append(
                split_dataset_cv(x, train_idx, validation_idx, "validation")
            )
            y_prepared.append(
                split_dataset_cv(y, train_idx, validation_idx, "validation")
            )

        # The trailing entry trains the final model. Its train partition is
        # every row the folds could use, and its test partition holds the rows
        # reserved for scoring and explaining that model, which is empty when
        # nothing was reserved.
        indice = {
            "train_indexes": fold_pool,
            "test_indexes": test_indexes,
        }
        indices["full_dataset"] = indice
        x_prepared.append(split_dataset_cv(x, fold_pool, test_indexes))
        y_prepared.append(split_dataset_cv(y, fold_pool, test_indexes))

        return x_prepared, y_prepared, indices
