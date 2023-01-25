from dataLoaderMain import DataLoader

class CSVDataLoader(DataLoader):
	"""
	Data loader for tabular data in CSV files
	"""
	TASKS = ["NumericClassificationTask", "TextClassificationTask"]

	def load_data(self, dataset_path, url = None):
		super().load_dataset("csv", dataset_path, url)

	def set_task_format(self, task):
		if task not in TASKS:
			raise Exception(f'This data loader is not for {task} task.')
		else:
			# call to format method in task class