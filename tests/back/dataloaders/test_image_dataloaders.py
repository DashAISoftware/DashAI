"""Dataloaders tests."""

import shutil

from datasets import DatasetDict
from starlette.datastructures import Headers, UploadFile

from DashAI.back.dataloaders.classes.image_dataloader import ImageDataLoader


def test_image_dataloader_from_zip():
    test_dataset_path = "tests/back/dataloaders/beans_dataset_small.zip"
    image_dataloader = ImageDataLoader()

    with open(test_dataset_path, "rb") as file:
        uploaded_file = UploadFile(
            filename=test_dataset_path,
            file=file,
            headers=Headers({"Content-Type": "application/zip"}),
        )

        dataset = image_dataloader.load_data(
            filepath_or_buffer=uploaded_file,
            temp_path="tests/back/dataloaders/beans_dataset_small",
            params={},
        )

    assert isinstance(dataset, DatasetDict)

    shutil.rmtree("tests/back/dataloaders/beans_dataset_small", ignore_errors=True)
