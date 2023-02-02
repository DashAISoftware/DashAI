import os
import io
import zipfile
from datasets import load_dataset, Image
from Dataloaders.classes.dataLoaderMain import DataLoader

class ImageDataLoader(DataLoader):
	"""
	Data loader for data from image files
	"""
	def load_data(self, dataset_path, params, file = None, url = None):
		if url:
			dataset = load_dataset("imagefolder", data_files=url).cast_column("image", Image(decode=False))
		elif file:
			if file.content_type == "application/zip":
				with zipfile.ZipFile(io.BytesIO(file.file.read()), 'r') as zip_file:
					zip_file.extractall(path=f"{dataset_path}/files")
				dataset = load_dataset("imagefolder", 
					data_dir=dataset_path+"/files").cast_column("image", Image(decode=False))
			else:
				raise Exception("For image data is necessary a zip file.")
		return dataset
		
	def set_task_format(self, task):
		pass # call to format method in task class