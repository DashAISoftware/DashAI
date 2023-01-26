from dataLoaderMain import DataLoader

class CSVDataLoader(DataLoader):
	"""
	Data loader for tabular data in CSV files
	"""
	TASKS = ["NumericClassificationTask", "TextClassificationTask"]

	def load_data(self, dataset_path, separator, url = None):
		if url:
			dataset = load_dataset("csv", data_files=url, sep=separator)
		else:
			dataset = load_dataset("csv", data_dir=dataset_path, sep=separator)
		dataset.save_to_disk(dataset_path+"_config")

	def set_task_format(self, task):
		if task not in TASKS:
			raise Exception(f'This data loader is not for {task} task.')
		else:
			# call to format method in task class