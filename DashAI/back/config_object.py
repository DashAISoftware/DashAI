from DashAI.back.core.schema_fields.base_schema import BaseSchema
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
        return cls.SCHEMA.model_json_schema()

    def validate_and_transform(self, raw_schema: dict) -> dict:
        schema_instance = self.SCHEMA.model_validate(raw_schema)
        return fill_objects(schema_instance)
