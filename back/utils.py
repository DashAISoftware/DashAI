from Models.classes.getters import filter_by_parent
from TaskLib.task.taskMain import Task

def get_model_params_from_task(task_name):
    """
    It returns a dictionary with a list of the available models for the
    task or an error if the squema
    """
    try:
        model_class_name = f"{task_name[:-4]}Model"
        dict = filter_by_parent(model_class_name)
        return {"models": list(dict.keys())}
    except:
        return {"error": f"{model_class_name} not found"}

def create_task(task_type) -> Task:
    """
    Maps the task_type to the corresponding Task object
    """
    return Task.createTask(task_type)