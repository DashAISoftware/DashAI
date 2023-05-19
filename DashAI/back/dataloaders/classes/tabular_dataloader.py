from datasets import ClassLabel, DatasetDict

from DashAI.back.dataloaders.classes.dataloader import BaseDataLoader


class TabularDataLoader(BaseDataLoader):
    """
    Intermediate class for tabular dataloaders methods
    """

    _compatible_tasks = ["TabularClassificationTask"]

    def set_classes(
        self, dataset: DatasetDict, class_column: str | int
    ) -> tuple[DatasetDict, str]:
        """
        Set the class column in the dataset.

        Args:
            dataset (DatasetDict): Dataset in Hugging Face format.
            class_column (str/int): Name or index of class column of the dataset.

        Returns:
            DatasetDict: Dataset with defined class column.
            str: Name of the class column.

        -------------------------------------------------------------------------------
        - NOTE: This method cast the class column as a ClassLabel, wich is
                necessary for do the stratify in splitting process with Hugging Face.
                Also, considerate that this method encodes the classes to numeric data,
                but you can retrieve the labels with conversion methods:
                - ClassLabel.int2str(): encoded labels to string labels
                - ClassLabel.str2int(): string labels to encoded labels

                More information:
                https://huggingface.co/docs/datasets/about_dataset_features
        --------------------------------------------------------------------------------
        """
        # Type checks
        if not isinstance(dataset, DatasetDict):
            raise TypeError(f"dataset should be a DatasetDict, got {type(dataset)}")
        if not (isinstance(class_column, str) or isinstance(class_column, int)):
            raise TypeError(
                f"class_column should be a integer or string, got {type(class_column)}"
            )

        # Check if class column exist
        columns = dataset["train"].column_names
        if isinstance(class_column, int) and class_column > len(columns):
            raise ValueError(
                f"Class column index {class_column} does not exist in dataset."
            )
        if isinstance(class_column, str) and class_column not in columns:
            raise ValueError(
                f"Class column '{class_column}' does not exist in dataset."
            )

        # Set class column
        for split in ["train", "test", "validation"]:
            if split in dataset:
                if isinstance(class_column, str):
                    label = class_column
                else:
                    label = dataset[split].column_names[class_column]
                new_features = dataset[split].features.copy()
                new_features[label] = ClassLabel(names=list(set(dataset[split][label])))
                dataset[split] = dataset[split].cast(new_features)
        return dataset, label

    def select_features(
        self, dataset: DatasetDict, selected_features: list[str]
    ) -> DatasetDict:
        """
        Remove the features (columns) not selected for the dataset

        Args:
            dataset (DatasetDict): Dataset in Hugging Face format.
            selected_features (array[str]): Names of columns of the features selected.

        Returns:
            DatasetDict: Dataset with only selected features.
        """
        # Type checks
        if not isinstance(dataset, DatasetDict):
            raise TypeError(f"dataset should be a DatasetDict, got {type(dataset)}")
        if not isinstance(selected_features, list):
            raise TypeError(
                "selected_features should be a list of strings,"
                + f" got {type(selected_features)}"
            )
        if any(not isinstance(e, str) for e in selected_features):
            raise TypeError("selected_features elements should be string.")

        # Check for features exists
        for feature in selected_features:
            if feature not in dataset["train"].column_names:
                raise ValueError(f"'{feature}' is not a feature of the dataset")

        # Remove not selected features
        for split in ["train", "test", "validation"]:
            columns = []
            if split in dataset:
                for feature in dataset[split].features:
                    if feature not in selected_features:
                        columns.append(feature)
            dataset[split] = dataset[split].remove_columns(columns)
        return dataset
