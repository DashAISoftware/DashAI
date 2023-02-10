from base.base_task import BaseTask


class TabularClassificationTask(BaseTask):
    """
    Tabular Classifitacion task.
    """

    name: str = "TabularClassificationTask"
    compatible_models = [] # TODO: find a better way to do this

    def parse_single_input_from_string(self, x_string: str):
        splited_x = x_string.split(",")
        output = []
        for x in splited_x:
            output.append(float(x))
        return [output]
