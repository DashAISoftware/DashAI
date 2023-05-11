import {
  getChildren as getChildrenRequest,
  getModelSchema as getModelSchemaRequest,
} from "../api/oldEndpoints";

export function getDefaultValues(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== "undefined") {
    const parameters = Object.keys(properties);
    const defaultValues = {};
    parameters.forEach((param) => {
      const val = properties[param].oneOf[0].default;
      defaultValues[param] = typeof val !== "undefined" ? val : { choice: "" };
    });
    return defaultValues;
  }
  return "null";
}

export async function getFullDefaultValues(
  parameterJsonSchema,
  choice = "none",
) {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== "undefined") {
    const parameters = Object.keys(properties);
    const defaultValues = choice === "none" ? {} : { choice };
    parameters.forEach(async (param) => {
      const val = properties[param].oneOf[0].default;
      if (val !== undefined) {
        defaultValues[param] = val;
      } else {
        const { parent } = properties[param].oneOf[0];

        const receivedOptions = await getChildrenRequest(parent);
        const [first] = receivedOptions;
        const parameterSchema = await getModelSchemaRequest(first);
        defaultValues[param] = await getFullDefaultValues(
          parameterSchema,
          first,
        );
      }
    });
    return defaultValues;
  }
  return {};
}
