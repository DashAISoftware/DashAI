from fastapi import APIRouter
from Dataloaders.classes.audioDataLoader import AudioDataLoader
from Dataloaders.classes.csvDataLoader import CSVDataLoader
from Dataloaders.classes.imageDataLoader import ImageDataLoader
from Dataloaders.dataLoadModel import DatasetParams

router = APIRouter()

def parse_params(params):
    """
    Parse JSON from string to pydantic model
    """
    try:
        model = DatasetParams.parse_raw(params)
        return model
    except pydantic.ValidationError as e:
        raise HTTPException(
            detail=jsonable_encoder(e.errors()),
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        ) from e


@router.get("/dataset/")
async def get_dataset():
    return [{"username": "Rick"}, {"username": "Morty"}]

@router.post("/dataset/")
async def upload_dataset(
    params: str = Form(), url: str = Form(None), file: UploadFile = File(None)
):
    session_id = 0  # TODO: generate unique ids
    params = parse_params(params)
    dataloader = globals()[params.data_loader]()
    folder_path = f"../datasets/{params.dataset_name}"
    os.mkdir(folder_path)
    try:
        dataset = dataloader.load_data(
            dataset_path=folder_path,
            params=params.dataloader_params.dict(),
            file=file,
            url=url,
        )
        dataset, class_column = dataloader.set_classes(dataset, params.class_index)
        if not params.folder_split:
            dataset = dataloader.split_dataset(
                dataset, params.splits.dict(), class_column
            )
        dataset.save_to_disk(folder_path + "/dataset")

        # TODO: add dataset to database register

        session_info[session_id] = {
            "dataset": params.dataset_name,
            "task_name": params.task_name,
            # TODO Task throw exception if createTask fails
            "task": Task.createTask(params.task_name),
        }
        # TODO give session_id to user
        return get_model_params_from_task(params.task_name)
    except OSError:
        os.remove(folder_path)
        return {"message": "Couldn't read file."}
