from Database import db
from sqlalchemy import Column, Integer, String, Float, JSON, LargeBinary

class Experiment(db.Base):
    __tablename__ = 'experiment'
    """
    Class to store all the information about the experiment 
    the user do. 
    """
    id = Column(Integer, primary_key=True)
    task_name = Column(String)
    dataset = Column(JSON)
    # executions = List(executions)

    def __init__(self, task_name, dataset):
        self.task_name = task_name
        self.dataset = dataset

class Execution(db.Base):
    __tablename__ = 'execution'
    """
    Class to store all the information about an specific execution.
    """
    id = Column(Integer, primary_key=True)
    parameters = Column(JSON)
    train_results = Column(JSON)
    test_results = Column(JSON)
    exec_bytes = Column(LargeBinary)

    def __init__(self, parameters, train_results, test_results, exec_bytes):
        self.parameters = parameters
        self.train_results = train_results
        self.test_results = test_results
        self.exec_bytes = exec_bytes
