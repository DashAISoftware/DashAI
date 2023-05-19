import json

from DashAI.back.core.enums.squema_types import SquemaTypes

dict_squemas = {
    SquemaTypes.model: "DashAI/back/models/parameters/models_schemas/",
    SquemaTypes.preprocess: "DashAI/back/models/parameters/preprocess_schemas",
    SquemaTypes.dataloader: "DashAI/back/dataloaders/params_schemas/",
    SquemaTypes.task: "DashAI/back/tasks/tasks_schemas/",
}


class ConfigObject:
    @staticmethod
    def get_squema(type, name):
        try:
            with open(f"{dict_squemas[type]}{name}.json") as f:
                return json.load(f)

        except FileNotFoundError:
            with open(f"{dict_squemas[type]}{name.lower()}.json"):
                return json.load(f)
