class TaskMetaclass(type):
    """
    MetaClass to define a class type which register itself into the
    registry_tasks list. It can create subclasses from the registry.
    """
    registry_tasks = {}
    def __new__(cls, name, bases, attrs):
        newtask = super().__new__(cls, name, bases, attrs)
        cls.registry_tasks[name] = newtask
        return newtask

    @classmethod
    def createTask(cls, task : str):
        try:
            created_task = cls.registry_tasks[task].create() # Task creates itself
            return created_task
        except:
            return f"{task} was not found in tasks registry"
