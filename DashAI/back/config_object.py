import json
import os

from DashAI.back.core.enums.squema_types import SquemaTypes

curr_path = os.path.dirname(os.path.realpath(__file__))
dashai_path = os.path.dirname(curr_path)

dict_squemas = {
    SquemaTypes.model: os.path.join(
        dashai_path, "back/models/parameters/models_schemas/"
    ),
    SquemaTypes.preprocess: os.path.join(
        dashai_path, "back/models/parameters/preprocess_schemas"
    ),
    SquemaTypes.dataloader: os.path.join(
        dashai_path, "back/dataloaders/params_schemas/"
    ),
    SquemaTypes.task: os.path.join(dashai_path, "back/tasks/tasks_schemas/"),
    SquemaTypes.global_explainer: os.path.join(
        dashai_path, "back/explainability/explainers_schemas/"
    ),
    SquemaTypes.local_explainer: os.path.join(
        dashai_path, "back/explainability/explainers_schemas/"
    ),
}


class ConfigObject:
    @staticmethod
    def get_squema(type, name):
        try:
            print(f"type: {type}, schema: {name}")
            with open(f"{dict_squemas[type]}{name}.json") as f:
                return json.load(f)

        except FileNotFoundError:
            with open(f"{dict_squemas[type]}{name.lower()}.json"):
                return json.load(f)
