from abc import abstractmethod
from configObject import ConfigObject
from datasets import ClassLabel

class DataLoader(ConfigObject):
	"""
	Abstract class with base methods for all data loaders
	"""
	@abstractmethod
	def load_data(self, dataset_path, url = None):
		pass
	
	@abstractmethod
	def set_task_format(self, task):
		pass

	def split_dataset(self, dataset, params):
		"""
		Split the dataset in train, test and validation data
		"""
		test_val = params["test"]+params["val"]
		val_size = params["val"]/test_val
		train_split = dataset["train"].train_test_split(
						test_size=test_val, 
						shuffle=params["shuffle"], 
						seed=params["seed"],
						stratify_by_column=params["stratify_column"]
						)
		test_valid_split = train_split['test'].train_test_split(
						test_size=val_size,
						shuffle=params["shuffle"],
						seed=params["seed"],
						stratify_by_column=params["stratify_column"]
						)
		dataset["train"] = train_split["train"]
		dataset["test"] = test_valid_split["train"]
		dataset["validation"] = test_valid_split["test"]
		return dataset

	def set_classes(self, dataset, classes):
		"""
		Set the class columns (for tabular data)
		"""
		for split in ["train", "test", "validation"]:
			if split in dataset:
				for label in classes:
					new_features = dataset[split].features.copy()
					new_features[label] = ClassLabel(names=list(set(dataset[split][label])))
				dataset[split] = dataset[split].cast(new_features)
		return dataset

	def select_features(self, dataset, selected_features):
		"""
		Remove the features not selected for the dataset (for tabular data)
		"""
		for split in ["train", "test", "validation"]:
		    columns = []
		    if split in dataset:
		        for feature in dataset[split].features:
		            if feature not in selected_features:
		                columns.append(feature)
		    dataset[split] = dataset[split].remove_columns(columns)
		return dataset