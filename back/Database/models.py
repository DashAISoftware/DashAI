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
    # TODO connect the experiment with its executions.
    # executions = List(executions)

    def __init__(self, task_name, dataset):
        self.task_name = task_name
        self.dataset = dataset
    
    # TODO create method get metrics, that retrieves the results from every execution.

class Execution(db.Base):
    __tablename__ = 'execution'
    """
    Class to store all the information about an specific execution.
    """
    id = Column(Integer, primary_key=True)
    parameters = Column(JSON)
    exec_filepath = Column(String)
    train_results = Column(JSON)
    test_results = Column(JSON)

    def __init__(self, parameters, exec_filepath, train_results = {}, test_results = {}):
        self.parameters = parameters
        self.exec_filepath = exec_filepath
        self.train_results = train_results
        self.test_results = test_results
    
    def set_results(self, train_results, test_results):
        """
        Method to change the results of the execution.
        """
        self.train_results = train_results
        self.test_results = test_results
        
