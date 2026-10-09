from collections import namedtuple

from kink import di

from DashAI.back.core.schema_fields.search_space import SEARCH_DTYPE_KEY
from DashAI.back.metrics.base_metric import BaseMetric
from DashAI.back.metrics.classification_metric import ClassificationMetric

#: What an optimizer needs to know about one parameter: the kind of
#: distribution to draw from, and the space to draw it out of.
_Space = namedtuple("_Space", ("values", "dtype"))


def _search_space_of(field_schema: dict, value: dict) -> _Space:
    """Read the declared search space for one optimizable parameter.

    The dtype used to be read off the JSON Schema ``type`` key, which is absent
    whenever a field admits null (pydantic emits ``anyOf`` instead) and cannot
    say "categorical" at all. ``search_space`` declares it explicitly; the
    ``type`` key stays as the fallback for the fields still declared the old
    way.

    An interval hands the optimizer a ``(low, high)`` pair; a set of options
    hands it the options. Both land in the same slot of the tuple the
    optimizers consume, so nothing downstream changes shape.
    """
    dtype = field_schema.get(SEARCH_DTYPE_KEY) or field_schema.get("type")
    if dtype == "categorical":
        return _Space(value.get("choices"), dtype)
    return _Space((value.get("lower_bound"), value.get("upper_bound")), dtype)


class ModelFactory:
    """
    A factory class for creating and configuring models.

    Attributes
    ----------
    fixed_parameters : dict
        A dictionary of parameters that are fixed and not intended to be optimized.
    optimizable_parameters : dict
        A dictionary of parameters that are intended to be optimized, with their
        respective lower and upper bounds.
    model : BaseModel
        An instance of the model initialized with the fixed parameters.

    Methods
    -------
    _extract_parameters(parameters: dict) -> tuple
        Extracts fixed and optimizable parameters from a dictionary.
    """

    def __init__(
        self,
        model,
        params: dict,
        run_id: id = None,
        x_data: dict = None,
        y_data: dict = None,
        train_metrics: list[BaseMetric] = None,
        validation_metrics: list[BaseMetric] = None,
        test_metrics: list[BaseMetric] = None,
        n_labels=None,
    ):
        """Initialise the factory, instantiate the model, and attach runtime state.

        Parameters
        ----------
        model : type
            A DashAI model class (not an instance) to instantiate with the
            extracted fixed parameters.
        params : dict
            Nested parameter dictionary as produced by the DashAI UI, containing
            ``fixed_value`` and optional ``optimizable`` sub-keys.
        run_id : id, optional
            Identifier of the associated experiment run. Default is ``None``.
        x_data : dict, optional
            Dataset splits for model input (``{"train": ..., "test": ...}``).
            Default is ``None``.
        y_data : dict, optional
            Dataset splits for model targets. Default is ``None``.
        train_metrics : list[BaseMetric], optional
            Metric instances to evaluate on the training split. Default is ``None``.
        validation_metrics : list[BaseMetric], optional
            Metric instances to evaluate on the validation split. Default is ``None``.
        test_metrics : list[BaseMetric], optional
            Metric instances to evaluate on the test split. Default is ``None``.
        n_labels : int, optional
            Number of unique class labels; used to determine whether the task is
            binary or multiclass. Default is ``None``.
        """
        self.model, self.fixed_parameters, self.optimizable_parameters = (
            self._extract_parameters(model, params)
        )

        # Set run id
        self.model.run_id = run_id

        # Set data for the model
        self.model.x_data = x_data
        self.model.y_data = y_data

        # Set metrics
        self.model.train_metrics = train_metrics
        self.model.validation_metrics = validation_metrics
        self.model.test_metrics = test_metrics

        self.num_labels = n_labels
        self.fitted = False

    def _extract_parameters(self, model_class, parameters: dict):
        """
        Recursively instantiate a DashAI model and
        its subcomponents from a parameters dict,
        and collect references to optimizable parameters
        including their ranges.

        Parameters
        ----------
        model_class : type
            The class of the model to instantiate.
        parameters : dict
            A dictionary of parameters for the model, which may include
            nested DashAI components and optimizable parameters.

        Returns
        -------
        tuple
            A tuple containing:
            - The instantiated model.
            - A dictionary of fixed parameters.
            - A list of tuples representing optimizable parameters,
              each containing
              (object reference, parameter name, (lower_bound, upper_bound)).
        """
        fixed_params = {}
        optimizable_refs = []

        # Instantiate main model without calling __init__
        model_instance = model_class.__new__(model_class)

        for key, val in parameters.items():
            fixed_val, refs = self._process_param(model_instance, key, val)
            fixed_params[key] = fixed_val
            optimizable_refs.extend(refs)

        # Initialize model with fixed params
        if hasattr(model_instance, "__init__"):
            model_instance.__init__(**fixed_params)

        return model_instance, fixed_params, optimizable_refs

    def _process_param(self, obj, key, value):
        """
        Recursively process each parameter and
        bind optimizable refs to the final model graph.

        Parameters
        ----------
        obj : object
            The object to which the parameter belongs.
        key : str
            The name of the parameter.
        value : any
            The value of the parameter, which may be a nested component,
            an optimizable parameter, or a fixed value.

        Returns
        -------
        tuple
            A tuple containing:
            - The fixed value of the parameter.
            - A list of tuples representing optimizable parameters,
              each containing
              (object reference, parameter name, (lower_bound, upper_bound)).
        """
        local_refs = []
        component_registry = di["component_registry"]

        component = {
            key: value
            for key, value in component_registry[obj.__class__.__name__].items()
            if key != "class"
        }
        component_params = component.get("schema").get("properties")

        # Unwrap 'properties' if present
        if isinstance(value, dict) and "properties" in value and len(value) == 1:
            value = value["properties"]

        # --- Case 1: Nested DashAI component ---
        if isinstance(value, dict) and "component" in value:
            parent_component_name = value["component"]
            component = value.get("params", {}).get("comp", {})

            if component == {}:
                component_name = parent_component_name
                params_dict = value.get("params", {})
            else:
                component_name = component.get("component")
                params_dict = component.get("params", {})

            sub_model_class = component_registry[component_name]["class"]

            # Recursively build the submodel
            sub_model_instance, _, sub_refs = self._extract_parameters(
                sub_model_class, params_dict
            )

            # Attach submodel to the *real* parent object
            setattr(obj, key, sub_model_instance)

            # Rebind all sub_refs to point to this same instance (no duplicates needed)
            local_refs.extend(sub_refs)
            fixed_val = sub_model_instance

        # --- Case 2: Optimizable parameter ---
        elif isinstance(value, dict) and value.get("optimize") is True:
            fixed_value = value.get("fixed_value")
            space = _search_space_of(component_params.get(key, {}), value)

            setattr(obj, key, fixed_value)
            local_refs.append((obj, key, space.values, space.dtype))

            fixed_val = fixed_value

        # --- Case 3: Fixed parameter ---
        elif isinstance(value, dict) and "fixed_value" in value:
            fixed_value = value["fixed_value"]
            setattr(obj, key, fixed_value)
            fixed_val = fixed_value

        # --- Case 4: Primitive value ---
        else:
            setattr(obj, key, value)
            fixed_val = value

        return fixed_val, local_refs

    def update_parameters(
        self,
        old_parameters: dict,
        new_params: dict,
    ) -> dict:
        """
        Update the old parameters of the model with new parameter
        values found during optimization.

        Parameters
        ----------
        old_parameters : dict
            A dictionary of the current parameters of the model,
            which may include nested DashAI components
            and optimizable parameters.

        new_params : dict
            A dictionary of new parameter values to update in the model,
            where keys correspond to parameter names and
            values are the new fixed values.

        Returns
        -------
            updated_parameters (dict): A dictionary with the updated parameters
            in the same format as old_parameters.

        """

        def recursive_update(params, param_name, new_value):
            """Recursively set ``fixed_value`` for a named parameter in a nested dict.

            Parameters
            ----------
            params : dict
                Nested parameter dictionary to search.
            param_name : str
                The key whose ``fixed_value`` should be updated.
            new_value : Any
                The new value to assign.

            Returns
            -------
            bool
                ``True`` if the parameter was found and updated; ``False`` otherwise.
            """
            for key, val in params.items():
                if isinstance(val, dict):
                    if key == param_name and "fixed_value" in val:
                        val["fixed_value"] = new_value
                        return True  # Stop searching after updating
                    if recursive_update(val, param_name, new_value):
                        return True
            return False

        updated_parameters = old_parameters.copy()
        for param_name, new_value in new_params.items():
            # Recursively search for the parameter in the old parameters dict
            recursive_update(updated_parameters, param_name, new_value)

        return updated_parameters

    def evaluate(self, x, y, metrics):
        """
        Computes metrics only if the model is fitted.

        Parameters
        ----------
        x : dict
            Dictionary with input data for each split.
        y : dict
            Dictionary with output data for each split.
        metrics : list
            List of metric classes to evaluate.

        Returns
        -------
        dict
            Dictionary with metrics scores for each split.
        """

        multiclass = None
        if hasattr(self, "num_labels") and self.num_labels is not None:
            multiclass = self.num_labels > 2

        results = {}
        for split in ["train", "validation", "test"]:
            split_results = {}
            if x[split].shape[0] == 0:
                split_results = {metric.__name__: None for metric in metrics}
                results[split] = split_results
                continue
            predictions = self.model.predict(x[split])
            if hasattr(self.model, "prepare_output"):
                transformed_y = self.model.prepare_output(y[split])
            else:
                transformed_y = self.model.prepare_dataset(y[split])
            for metric in metrics:
                if (
                    isinstance(metric, type)
                    and issubclass(metric, ClassificationMetric)
                    and "multiclass" in metric.score.__code__.co_varnames
                    and multiclass is not None
                ):
                    score = metric.score(
                        transformed_y, predictions, multiclass=multiclass
                    )
                else:
                    score = metric.score(transformed_y, predictions)

                split_results[metric.__name__] = score

            results[split] = split_results

        return results
