import type {
  IParameterJsonSchema,
  IDefaultValues,
} from "../types/configurableObject";
import {
  getChildren as getChildrenRequest,
  getModelSchema as getModelSchemaRequest,
} from "../api/oldEndpoints";

export const getFullDefaultValues = async (
  parameterJsonSchema: IParameterJsonSchema,
  choice: string = "none",
): Promise<object> => {
  const { properties } = parameterJsonSchema;

  if (properties === undefined || Object.keys(properties).length === 0) {
    return {};
  }

  const defaultValues: IDefaultValues = choice === "none" ? {} : { choice };

  for (const param of Object.keys(properties)) {
    const val = properties[param].oneOf[0].default;

    if (val !== undefined) {
      defaultValues[param] = val;
    } else {
      const { parent } = properties[param].oneOf[0];
      let options: string[];
      let parameterSchema: IParameterJsonSchema;

      try {
        if (parent !== undefined) {
          options = await getChildrenRequest(parent);
        } else {
          options = [];
        }
        const [first] = options;

        parameterSchema = await getModelSchemaRequest(first);

        defaultValues[param] = await getFullDefaultValues(
          parameterSchema,
          first,
        );
      } catch (error) {
        console.error(error);
      }
    }
  }

  return defaultValues;
};
