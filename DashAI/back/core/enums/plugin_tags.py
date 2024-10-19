from enum import Enum


class PluginTag(Enum):
    DashAI = "DashAI"
    Package = "Package"
    Task = "Task"
    Model = "Model"
    Metric = "Metric"
    Dataloader = "Dataloader"
    Converter = "Converter"
    Explainer = "Explainer"
