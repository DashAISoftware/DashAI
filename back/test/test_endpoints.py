import pytest
import sys
from fastapi.testclient import TestClient
from hypothesis import given
from hypothesis.strategies import text, integers
sys.path.append('../back')
from main import app


client = TestClient(app)

def test_upload_dataset_string():
    response = client.post("/dataset/upload/IMDB")
    assert response.status_code == 422
    #assert response.json() == {"models": ["knn","naive_bayes","random_forest"]}

@given(integers())
def test_upload_dataset_int(i):
    response = client.post("/dataset/upload/"+str(i))
    assert response.status_code == 200
    #assert response.json() == {"models": ["knn","naive_bayes","random_forest"]}

def test_select_dataset():
    response = client.get("/selectModel/knn")
    assert response.status_code == 200    