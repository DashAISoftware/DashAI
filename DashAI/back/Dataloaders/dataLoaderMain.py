from abc import abstractmethod
from configObject import ConfigObject
from datasets import load_dataset, load_from_disk

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

	def split_dataset(self, dataset_path, params):
		"""
		Split the dataset in train, test and validation data
		"""
		dataset = load_from_disk(dataset_path+"_config")
		test_val = params["test"]+params["val"]
		val_size = params["val"]/testval
		train_split = dataset.train_test_split(
						test=test_val, 
						shuffle=params["shuffle"], 
						seed=params["seed"]
						)
		test_valid_split = train_split['test'].train_test_split(
						test=val_size,
						shuffle=params["shuffle"],
						seed=patams["seed"])
		dataset["train"] = train_split["train"]
		dataset["test"] = test_valid_split["train"]
		dataset["validation"] = test_valid_split["test"]
		dataset.save_to_disk(dataset_path+"_config")

	def set_classes(self, dataset_path, classes):
		"""
		Set the class columns (for tabular data)
		"""
		dataset = load_from_disk(dataset_path+"_config")
		for split in ["train", "test", "validation"]:
			for label in classes:
				new_features = dataset[split].features.copy()
				new_features[label] = ClassLabel(names=list(set(dataset[split][label])))
			dataset = dataset.cast(new_features)
		dataset.save_to_disk(dataset_path+"_config")

	def select_features(self, dataset_path, selected_features):
		"""
		Remove the features not selected for the dataset (for tabular data)
		"""
		dataset = load_from_disk(dataset_path+"_config")
		for split in ["train", "test", "validation"]:
		    columns = []
		    try:
		        for feature in dataset[split].features:
		            if feature not in selected_features:
		                columns.append(feature)
		    except: continue
		    dataset[split] = dataset[split].remove_columns(columns)
		dataset.save_to_disk(file+"_config")