from importlib import import_module
from inspect import isclass
from pkgutil import iter_modules

class FindByParent():

    def __init__(self, *classes_dict):
        self.classes_dict = {}
        for d in classes_dict:
            self.classes_dict = {**self.classes_dict, **d}
        print(self.classes_dict)

    def get_children(self, parent_class_name):
        filtered_dict = {}
        for class_obj in self.classes_dict.values():
            if parent_class_name in map(lambda x: x.__name__, class_obj.__bases__):
                filtered_dict[class_obj.__name__] = class_obj
        return filtered_dict