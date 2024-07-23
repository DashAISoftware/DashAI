from pydantic import BaseModel


def replace_defs_in_schema(schema: dict):
    if "$defs" in schema:
        for prop in schema["properties"]:
            if "$ref" in schema["properties"][prop]:
                _, _, def_name = schema["properties"][prop]["$ref"].split("/")
                schema["properties"][prop] = schema["$defs"][def_name]
                schema["properties"][prop]["title"] = prop.title().replace("_", " ")
        schema.pop("$defs")
    return schema


class BaseSchema(BaseModel):
    pass
