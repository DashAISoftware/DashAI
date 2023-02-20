from datasets import load_dataset

class CSVDataLoader:
	"""
	Dataloader for load tabular data from CSV files
	"""
	def load_data(self, dataset_path, url = None):
		if url is None:
			dataset = load_dataset("csv", data_dir=dataset_path)
		else:
			dataset = load_dataset("csv", data_files=url)
		dataset.save_to_disk("dataset_path")

	def configure_dataset(self, dataset_path, parameters):
		# TODO: configure features an classes
		return None
	def split_data(self, dataset_path, parameters):
		# TODO: split dataset
		return None