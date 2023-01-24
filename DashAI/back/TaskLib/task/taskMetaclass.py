import logging

logging.basicConfig(level=logging.DEBUG)
log = logging.getLogger(__name__)


class TaskMetaclass(type):
    """
    MetaClass to define a class type which register itself into the
    registry_tasks list. It can create subclasses from the registry.
    """

    registry_tasks = {}

    def __new__(cls, name, bases, attrs):
        log.debug("Called metaclass: %r" % cls)
        log.debug("Creating class with name: %r" % name)
        newtask = super().__new__(cls, name, bases, attrs)
        log.debug("Registering class: %r" % newtask)
        cls.registry_tasks[name] = newtask
        log.debug("Class registry: ")
        log.debug(cls.registry_tasks)
        return newtask

    @classmethod
    def createTask(cls, task: str):
        try:
            log.debug(cls.registry_tasks[task])
            created_task = cls.registry_tasks[task].create()  # Task creates itself
            return created_task
        except TypeError:
            return f"{task} was not found in tasks registry"
