from abc import abstractmethod
from configObject import ConfigObject
from datasets import load_dataset, load_from_disk

class DataLoader(ConfigObject):
	"""
	Abstract class with base methods for all data loaders
	"""
	def load_data(self, file_type, dataset_path, url = None):
		if url:
			dataset = load_dataset(file_type, data_files=url)
		else:
			dataset = load_dataset(file_type, data_dir=dataset_path)
		dataset.save_to_disk(dataset_path)

	def set_classes(self, dataset_path, classes):
		dataset = load_from_disk(dataset_path)
		for label in classes: # TODO: expand to test, validation and train splits
			new_features = dataset["train"].features.copy()
			new_features[label] = ClassLabel(names=list(set(dataset["train"][label])))
		dataset = dataset.cast(new_features)
		# TODO: override files of huggingface dataset in disk

	def select_features(self, dataset_path, features):
		# TODO: configure features
		return None

	def split_dataset(self, dataset_path, parameters):
		# TODO: split dataset
		return None

	@abstractmethod
	def set_task_format(self, task):
		pass