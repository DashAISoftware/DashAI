from datasets import Dataset, Value


class Preprocessor:
    def __init__(self, dataset: Dataset):
        """
        Inicializa el preprocesador con un dataset.
        """
        self.dataset: Dataset = dataset

    def drop_columns(self, indexs: list(int)):
        """
        Elimina las columnas relacionadas con los index especificados del
        dataset.
        """
        for index in indexs:
            # first we will select the column names
            column_name = self.dataset.column_names[index]
            # then we will drop the column
            self.dataset = self.dataset.remove_columns(column_name)
        return self.dataset

    def rename_columns(self, columns: dict):
        """
        Renombra las columnas especificadas del dataset.
        """
        for old_name, new_name in columns.items():
            self.dataset = self.dataset.rename_column(old_name, new_name)
        return self.dataset

    def change_type(self, columns: dict):
        """
        Cambia el tipo de dato de las columnas especificadas del dataset.
        """
        new_features = self.dataset.features.copy()
        for column, new_type in columns.items():
            new_features[column] = Value(new_type)
        self.dataset = self.dataset.cast(new_features)
        return self.dataset
