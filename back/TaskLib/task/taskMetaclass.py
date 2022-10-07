class TaskMetaclass(type):
    """
    MetaClass to define a class type which register itself into the
    registry_tasks list. It can create subclasses from the registry.
    """
    registry_tasks = {}
    def __new__(cls, name, bases, attrs):
        print("Called metaclass: %r" % cls)
        print("Creating class with name: %r" % name)
        newtask = super().__new__(cls, name, bases, attrs)
        print("Registering class: %r" % newtask)
        cls.registry_tasks[name] = newtask
        print("Class registry: ")
        print(cls.registry_tasks)
        return newtask

    @classmethod
    def createTask(cls, task : str):
        try:
            print(cls.registry_tasks[task])
            created_task = cls.registry_tasks[task].create() # Task creates itself
            return created_task
        except:
            return f"{task} was not found in tasks registry"
