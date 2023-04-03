import pytest
from DashAI.back.database.models import Dataset

@pytest.fixture(scope="module")
def setup_experiments():
    # Create Dummy Dataset
    # - Create the dummy dataset directly to the DB
    dataset_id = None
    yield dataset_id
    # Delete the dataset
    # - delete the dataset from the test db

def test_create_experiment(client):
    # Create Experiment using the dummy dataset
    # - Set the dataset of the experiment as dummy dataset
    # - (Optional) Set the task_name as TabularClassificationTask

    # Create Experiment using the dummy dataset
    # - Set the dataset of the experiment as dummy dataset
    # - (Optional) Set the task_name as TabularClassificationTask

    # Check the params of the both experiments
    # - id -> default id
    # - dataset_id -> equal to dummy dataset id
    # - task_name -> equal to input task_name
    # - step -> inital step or TASK_SELECTION
    # - created = last_modified = now
    # - runs -> Empty list
    pass

def test_get_all_experiments(client):
    # Get all the experiments available in the back
    # - Check both experiment were uploaded succesfully
    pass

def test_get_wrong_experiment(client):
    # Try to retrieve a non-existent experiment an get an error
    pass

def test_modify_experiment(client):
    # Modify an existen experiment
    # - modify the task_name
    # - (Optional) modify the actual step

    # Get the experiment
    # - check the dataset is didn't change
    # - check the task_name changes
    # - (optional) check the actual step changes
    # - check the last_modified changes to now
    pass


def test_delete_experiment(client):
    # Delete the first experiment in the db
    # Check the status code
    # Get all dataset and check it isn't in the data
    pass
