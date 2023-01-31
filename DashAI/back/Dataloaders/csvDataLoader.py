from datasets import load_dataset
from Dataloaders.dataLoaderMain import DataLoader

class CSVDataLoader(DataLoader):
	"""
	Data loader for tabular data in CSV files
	"""
	def load_data(self, dataset_path, separator, url = None):
		if url:
			dataset = load_dataset("csv", data_files=url, sep=separator)
		else:
			dataset = load_dataset("csv", data_dir=dataset_path, sep=separator)
		dataset.save_to_disk(dataset_path)
		
	def set_task_format(self, task):
		pass # call to format method in task class