import json
from abc import ABCMeta

from src.models.enums.squema_types import SquemaTypes

dict_squemas = {
    SquemaTypes.model: "src/models/parameters/models_schemas/",
    SquemaTypes.preprocess: "src/models/parameters/preprocess_schemas",
}


class ConfigObject(metaclass=ABCMeta):
    @staticmethod
    def get_squema(type, name):
        try:
            f = open(f"{dict_squemas[type]}{name}.json")
        except:
            f = open(f"{dict_squemas[type]}{name.lower()}.json")
        return json.load(f)
