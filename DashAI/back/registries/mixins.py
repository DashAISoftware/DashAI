from typing import List, Type


class RegisterInTaskCompatibleComponentsMixin:
    def register_in_task_compatible_components(self, new_component: Type):
        if not hasattr(new_component, "_compatible_tasks"):
            raise AttributeError(
                f"Component {new_component.__name__} has no _compatible_tasks "
                "attribute."
            )

        if not isinstance(new_component._compatible_tasks, list):
            raise TypeError(
                f"Component {new_component.__name__} _compatible_tasks should be a "
                f"list, got {new_component._compatible_tasks} "
            )

        compatible_tasks: List[str] = new_component._compatible_tasks

        if len(compatible_tasks) == 0:
            raise ValueError(
                f"Component {new_component.__name__} has no associated tasks."
            )

        # register the model in each compatible tasks.
        for task_name in compatible_tasks:
            # check if the task exists in the registry.
            if task_name not in self._task_registry.registry:
                raise ValueError(
                    f"Error while trying to register {new_component.__name__} "
                    f"into {task_name}: "
                    f"{task_name} does not exists in the task registry."
                )

            # add compatible component.
            current_task = self._task_registry.registry[task_name]
            current_task.add_compatible_component(
                registry_for=self.registry_for,
                component=new_component,
            )
