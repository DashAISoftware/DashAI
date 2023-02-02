from abc import abstractmethod
from configObject import ConfigObject
from datasets import load_from_disk, ClassLabel

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

	def split_dataset(self, dataset, params, class_column):
		"""
		Split the dataset in train, test and validation data
		"""
		stratify_column = None
		if params["stratify"]:
			stratify_column = class_column
		test_val = params["test_size"]+params["val_size"]
		val_size = params["val_size"]/test_val
		train_split = dataset["train"].train_test_split(
						test_size=test_val, 
						shuffle=params["shuffle"], 
						seed=params["seed"],
						stratify_by_column=stratify_column
						)
		test_valid_split = train_split['test'].train_test_split(
						test_size=val_size,
						shuffle=params["shuffle"],
						seed=params["seed"],
						stratify_by_column=stratify_column
						)
		dataset["train"] = train_split["train"]
		dataset["test"] = test_valid_split["train"]
		dataset["validation"] = test_valid_split["test"]
		return dataset

	def set_classes(self, dataset, class_index):
		"""
		Set class column (for tabular data)
		"""
		for split in ["train", "test", "validation"]:
			if split in dataset:
				label = dataset[split].column_names[class_index]
				new_features = dataset[split].features.copy()
				new_features[label] = ClassLabel(names=list(set(dataset[split][label])))
				dataset[split] = dataset[split].cast(new_features)
		return dataset, label

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