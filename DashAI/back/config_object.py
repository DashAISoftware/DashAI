from DashAI.back.core.schema_fields.base_schema import BaseSchema


class ConfigObject:
    """Abstract class that all the DashAI components inherits."""

    SCHEMA: BaseSchema

    @classmethod
    def get_schema(cls) -> dict:
        """Generates the component related Json Schema.

        Returns
        --------
        dict
            Dictionary representing the Json Schema of the component.
        """
        return cls.SCHEMA.model_json_schema()
