from kink import di

from DashAI.back.core.schema_fields.base_schema import (
    BaseSchema,
    replace_defs_in_schema,
)
from DashAI.back.core.schema_fields.utils import fill_objects


class ConfigObject:
    """Abstract class that all the DashAI components inherits."""

    SCHEMA: BaseSchema = BaseSchema

    @classmethod
    def get_schema(cls) -> dict:
        """Generates the component related Json Schema.

        Returns
        --------
        dict
            Dictionary representing the Json Schema of the component.
        """
        schema = cls.SCHEMA.model_json_schema()
        return replace_defs_in_schema(schema)

    def validate_and_transform(self, raw_data: dict) -> dict:
        """It takes the data given by the user to initialize the model and
        returns it with all the objects that the model needs to work.

        To do this this function has two steps:
        - Validates the raw_data against the model schema,
        this process may throw a ValidatationError exception.
        - It transforms the validated data,
        changing the promised objects by the initialized objects.

        Parameters
        --------
        raw_data : dict
            A dictionary with the data provided by the user to initialize the model.

        Returns
        --------
        dict
            A validated dictionary with the necessary objects.

        Raises
        ------
        ValidationError
            If the given data does not follow the schema associated with the model.
        """
        try:
            from pydantic import ValidationError

            schema_instance = self.SCHEMA.model_validate(raw_data)
        except ValidationError as e:
            # print full error message
            print(e.json())
            raise e
        return fill_objects(schema_instance)

    def get_credential(self, name: str):
        """Resolve a registered credential component by name.

        The returned instance exposes ``get_key``, ``is_authenticated`` and
        ``apply``. When nothing is stored, ``get_key`` returns None and
        ``apply`` is a no-op, so optional credentials degrade gracefully.

        Parameters
        ----------
        name : str
            Credential component class name (e.g. "HuggingFaceCredential").

        Returns
        -------
        BaseCredential
            An instance of the requested credential component.
        """
        registry = di["component_registry"]
        credential_class = registry[name]["class"]
        return credential_class()
