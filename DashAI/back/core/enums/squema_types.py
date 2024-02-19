from enum import Enum


class SquemaTypes(Enum):
    model = "model"
    preprocess = "preprocess"
    tokenizer = "tokenizer"
    dataloader = "dataloader"
    task = "task"
    global_explainer = "global_explainer"
    local_explainer = "localexplainer"
