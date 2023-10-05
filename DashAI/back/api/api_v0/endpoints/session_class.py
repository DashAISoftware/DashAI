# TODO Remove this, only a placeholder
# maybe this can give an insight of the future orchestator
class Session:
    dataset = None
    task_name = ""
    task = None

    def state(self):
        return {"dataset": self.dataset, "task_name": self.task_name, "task": self.task}


session_info = Session()  # TODO Remove this
