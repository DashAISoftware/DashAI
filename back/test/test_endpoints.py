import pytest
import sys
from fastapi.testclient import TestClient
from fastapi import Path
from hypothesis import given
from hypothesis.strategies import text, integers
sys.path.append('../back')
from main import app

client = TestClient(app)

def test_state():
    response = client.get("/info")
    assert response.status_code == 200
    assert response.json() == {"state" : "online"}

def test_upload_dataset():
    _test_upload_file = open('./example_dataset/dummy_dataset.json')
    _files = {'file': _test_upload_file}
    response = client.post("/dataset/upload/", files=_files)
    assert response.status_code == 200
    #assert response.json() == {"models": ["knn","naive_bayes","random_forest"]}

@given(integers())
def test_upload_dataset_int(i): # TODO Test this when endpoint is working
    response = client.post("/dataset/upload/"+str(i))
    assert response.status_code == 200

def test_available_models_for_tasks():
    _models = ["TestTask"]
    for index, model in enumerate(_models):
        response = client.get("/models/"+model)
        assert response.status_code == 200
        assert "error" in response.json().keys()

def test_select_dataset():
    _models = ["knn", "numericalwrapperfortext", "randomforest", "svm"]
    _test_text = ["KNN", "NumericalWrapperForText", "RF", "SVM"]
    for index, model in enumerate(_models):
        response = client.get("/selectModel/"+model)
        assert response.status_code == 200
        assert _test_text[index] in response.json()["description"]
