from Database import db
from sqlalchemy import Column, Integer, String, JSON, ForeignKey
from sqlalchemy.orm import relationship

class Experiment(db.Base):
    __tablename__ = 'experiment'
    """
    Class to store all the information about the experiment 
    the user do. 
    """
    id = Column(Integer, primary_key=True)
    task_name = Column(String)
    dataset = Column(JSON)
    executions = relationship("Execution", back_populates="experiment")

    def __init__(self, task_name, dataset):
        self.task_name = task_name
        self.dataset = dataset
    
    def get_results(self):
        results = {}
        for execution in self.executions:
            results[execution.id] = {
                "train": execution.train_results,
                "test": execution.test_results,
            }
        return results

class Execution(db.Base):
    __tablename__ = 'execution'
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
    
    def __init__(self, experiment_id, parameters, exec_filepath = "", train_results = {}, test_results = {}):
        self.experiment_id = experiment_id
        self.parameters = parameters
        self.exec_filepath = exec_filepath
        self.train_results = train_results
        self.test_results = test_results
