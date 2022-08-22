from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

origins = [
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_info = {}

@app.post("/dataset/upload/{dataset}")
async def upload_dataset(dataset: str):
    session_id = 0
    print(dataset)
    session_info[session_id] = dataset 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.post("/dataset/upload/{dataset_id}")
async def upload_dataset(dataset_id: int):
    session_id = 0
    session_info[session_id] = dataset_id 
    return {"models": ["knn","naive_bayes","random_forest"]}

@app.post("/selectModel/{model_name}")
async def select_model(model_name : str):
    #return model_name.get_parameters()
    "Models/parameters/models_schemas/{selected_exec}.json"

@app.post("/selectedParameters/{model_name}")
async def select_model(model_name : str, parameters_json):
    return 


@app.post("/upload")
async def upload_test(file: UploadFile = File()):
    try:
        contents = file.file.read()
        with open(file.filename, 'wb') as f:
            f.write(contents)
    except:
        return {"message": "There was an error uploading the file"}
    finally:
        file.file.close()

    return {"message": f"Succesfully uploaded {file.filename}"}


@app.get("/experiment/results/{session_id}")
async def get_results(session_id: int):
    return {"knn": {"accuracy": 0.8, "precision": 0.7, "recall": 0.9}}
