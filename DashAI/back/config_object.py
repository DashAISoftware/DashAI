import json
from abc import ABCMeta

from DashAI.back.models.enums.squema_types import SquemaTypes

dict_squemas = {
    SquemaTypes.model: "DashAI/back/models/parameters/models_schemas/",
    SquemaTypes.preprocess: "DashAI/back/models/parameters/preprocess_schemas",
    SquemaTypes.dataloader: "DashAI/back/dataloaders/params_schemas/",
    SquemaTypes.task: "DashAI/back/tasks/tasks_schemas/",
}


class ConfigObject(metaclass=ABCMeta):
    @staticmethod
    def get_squema(type, name):
        try:
            f = open(f"{dict_squemas[type]}{name}.json")
        except FileNotFoundError:
            f = open(f"{dict_squemas[type]}{name.lower()}.json")
        return json.load(f)
