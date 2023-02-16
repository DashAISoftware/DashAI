from Database import db
from sqlalchemy import JSON, Column, ForeignKey, Integer, String
from sqlalchemy.orm import relationship


class Dataset(db.Base):
    __tablename__ = "dataset"
    """
    Class to store all the information about a dataset.
    """
    id = Column(Integer, primary_key=True)
    name = Column(String)
    task_name = Column(String)
    path = Column(String)

    def __init__(self, dataset_name, task_name, path=""):
        self.name = dataset_name
        self.task_name = task_name
        self.path = path


class Experiment(db.Base):
    __tablename__ = "experiment"
    """
    Class to store all the information about the experiment
    the user do.
    """
    id = Column(Integer, primary_key=True)
    dataset = Column(JSON)
    task_filepath = Column(String)
    executions = relationship("Execution", back_populates="experiment")

    def __init__(self, dataset, task_filepath=""):
        self.dataset = dataset
        self.task_filepath = task_filepath

    def get_results(self):
        results = {}
        for execution in self.executions:
            results[execution.id] = {
                "train": execution.train_results,
                "test": execution.test_results,
            }
        return results


class Execution(db.Base):
    __tablename__ = "execution"
    """
    Class to store all the information about an specific execution.
    """
    id = Column(Integer, primary_key=True)
    experiment_id = Column(Integer, ForeignKey("experiment.id"))
    experiment = relationship("Experiment", back_populates="executions")
    parameters = Column(JSON)
    exec_filepath = Column(String)
    train_results = Column(JSON)
    test_results = Column(JSON)

    def __init__(
        self,
        experiment_id,
        parameters,
        exec_filepath="",
        train_results={},
        test_results={},
    ):
        self.experiment_id = experiment_id
        self.parameters = parameters
        self.exec_filepath = exec_filepath
        self.train_results = train_results
        self.test_results = test_results
