from importlib import import_module
from inspect import isclass
from pathlib import Path
from pkgutil import iter_modules

from Models.classes import base_path


def introspect_classes():
    classes_dict = {}

    # iterate through the modules in the current package
    package_dir = Path(__file__).resolve().parent
    for (_, module_name, _) in iter_modules([str(package_dir)]):
        # import the module and iterate through its attributes
        module = import_module(f"{base_path}.{module_name}")
        for attribute_name in dir(module):
            attribute = getattr(module, attribute_name)

            if isclass(attribute):
                # Add the class to this package's variables
                class_name = attribute.__name__
                if class_name not in classes_dict.keys():
                    classes_dict[class_name] = attribute

    return classes_dict


def filter_by_parent(parent_class_name):
    class_dict = introspect_classes()
    parent_class = class_dict[parent_class_name]
    filtered_dict = {}

    for class_name in class_dict.keys():
        if (
            issubclass(class_dict[class_name], parent_class)
            and parent_class_name != class_name
        ):
            filtered_dict[class_name] = class_dict[class_name]

    return filtered_dict


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
