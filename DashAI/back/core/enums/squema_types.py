from enum import Enum


class SquemaTypes(Enum):
    model = "model"
    preprocess = "preprocess"
    tokenizer = "tokenizer"
    dataloader = "dataloader"
    task = "task"
    explainer = "explainer"
    explainer_fit_parameters = "explainer_fit_parameters"
