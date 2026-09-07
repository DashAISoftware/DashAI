from pydantic import BaseModel

from DashAI.back.core.utils import MultilingualString


def replace_defs_in_schema(schema: dict):
    # 1. Resolve $defs if present
    if "$defs" in schema:
        for prop, prop_schema in schema["properties"].items():
            if "$ref" in prop_schema:
                _, _, def_name = prop_schema["$ref"].split("/")
                schema["properties"][prop] = schema["$defs"][def_name]
        schema.pop("$defs")

    # 2. Normalize titles for ALL properties
    for prop, prop_schema in schema["properties"].items():
        # Extract display_name from the property level
        display_name = prop_schema.pop("display_name", None)

        # Also check inside anyOf/oneOf/allOf items
        for key in ["anyOf", "oneOf", "allOf"]:
            if key in prop_schema:
                for item in prop_schema[key]:
                    if "display_name" in item:
                        # Use the first display_name found if not already set
                        if display_name is None:
                            display_name = item.pop("display_name")
                        else:
                            item.pop("display_name")

        # Convert display_name to MultilingualString title
        if isinstance(display_name, MultilingualString):
            prop_schema["title"] = display_name
        elif isinstance(display_name, dict):
            prop_schema["title"] = MultilingualString(**display_name)
        elif isinstance(prop_schema.get("title"), MultilingualString):
            # already correct
            pass
        else:
            # fallback: derive from property name
            fallback_title = prop.replace("_", " ").title()
            prop_schema["title"] = MultilingualString(en=fallback_title)

    return schema


class BaseSchema(BaseModel):
    """@classmethod
    def model_validate(cls, raw_data: dict):
        schema_fields = cls.model_fields
        for field_name, field in schema_fields.items():
            if field_name not in raw_data:
                continue
            if field.annotation._name == 'Optional':
                if raw_data[field_name] == "":
                    raw_data[field_name] = None

        return super().model_validate(raw_data)"""
