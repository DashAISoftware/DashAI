import * as Yup from "yup";
import { getComponents } from "../api/component";

export async function resolveDefaults(
  modelName,
  { throwOnError = false } = {},
) {
  try {
    const result = await getComponents({ model: modelName });
    const info = Array.isArray(result) ? result[0] : result;
    if (!info?.schema) return {};
    const formatted = await formattedModel(info.schema);
    const { initialValues } = generateYupSchema(formatted);
    return initialValues;
  } catch (e) {
    console.warn(`[resolveDefaults] Failed for ${modelName}:`, e);
    if (throwOnError) throw e;
    return {};
  }
}

// Generate a Yup schema from a JSON schema object based on the JSON schema specification from the api, it also generates the initial values of the form
export const generateYupSchema = (schemaObj) => {
  const schema = {};
  const initialValues = {};

  // Iterate over the properties of the schema object
  Object.keys(schemaObj).forEach((key) => {
    const subSchema = schemaObj[key];
    const field = generateField(subSchema);
    schema[key] = field;
    initialValues[key] = generateInitialValues(subSchema);
  });

  return { schema: Yup.object().shape(schema), initialValues };
};

export const generateInitialValues = (subSchema) => {
  let initialValues = {};

  // Special case for optimizable fields
  if (subSchema.placeholder?.optimize !== undefined) {
    initialValues = subSchema.placeholder;
  } else if (subSchema.type !== "object") {
    initialValues = subSchema.placeholder;
  } else if (subSchema.parent) {
    // If the object has a parent, we need to create the initial values accordingly
    initialValues = {
      properties: {
        component: subSchema.properties.component,
        params: {
          comp: {
            component: subSchema.properties.params.comp.component,
            params: Object.keys(subSchema.properties.params.comp.params).reduce(
              (acc, current) => {
                acc[current] = generateInitialValues(
                  subSchema.properties.params.comp.params[current],
                );
                return acc;
              },
              {},
            ),
          },
        },
      },
    };
  } else {
    initialValues = Object.keys(subSchema.properties).reduce((acc, current) => {
      acc[current] = generateInitialValues(subSchema.properties[current]);
      return acc;
    }, {});
  }
  return initialValues;
};

const generateField = (subSchema) => {
  let field;

  // SPECIAL CASE: If it has placeholder.optimize, it is an optimizable field
  // It must be validated as an object regardless of the declared type
  if (subSchema.placeholder?.optimize !== undefined) {
    // Create base validators for optimizer fields with min/max constraints
    let fixedValueValidator = Yup.number().nullable();
    let lowerBoundValidator = Yup.number().nullable();
    let upperBoundValidator = Yup.number().nullable();

    // Apply min/max constraints from the schema to each field
    fixedValueValidator = applyMinMax(
      fixedValueValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    lowerBoundValidator = applyMinMax(
      lowerBoundValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    upperBoundValidator = applyMinMax(
      upperBoundValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    field = Yup.object()
      .shape({
        fixed_value: fixedValueValidator,
        lower_bound: lowerBoundValidator,
        upper_bound: upperBoundValidator,
        optimize: Yup.boolean(),
      })
      .test(
        "bounds-validation",
        "Lower bound must be less than or equal to upper bound",
        function (value) {
          if (!value) return true;
          const { lower_bound, upper_bound } = value;

          // Only validate if both bounds are defined
          if (lower_bound != null && upper_bound != null) {
            return lower_bound <= upper_bound;
          }
          return true;
        },
      );

    // Apply required validation if necessary
    if (subSchema.required) {
      field = field.required();
    }

    return field;
  }

  // For normal fields (non-optimizable)
  if (subSchema.anyOf) {
    field = Yup.mixed().nullable();
  } else if (subSchema.type === "object") {
    field = Yup.object();

    if (!subSchema.parent) {
      const properties = {};
      Object.keys(subSchema.properties).forEach((key) => {
        properties[key] = generateField(subSchema.properties[key]);
      });
      field = field.shape(properties);
    } else {
      field = getValidator(subSchema);
    }
  } else {
    field = getValidator(subSchema);
  }

  return field;
};

const getTypeValidator = (type) => {
  switch (type) {
    case "integer":
      return Yup.number().integer();
    case "number":
      return Yup.number();
    case "array":
      return Yup.array();
    case "string":
      return Yup.string();
    case "boolean":
      return Yup.boolean();
    case "null":
      return Yup.mixed().nullable();
    case "object":
      return Yup.object();
    default:
      throw new Error(`Unsupported type: ${type}`);
  }
};

const applyRequired = (validator, required) => {
  if (required) {
    return validator.required();
  }
  return validator;
};

const applyEnum = (validator, enumValues) => {
  if (enumValues) {
    return validator.oneOf(enumValues);
  }
  return validator;
};

const applyMinMax = (
  validator,
  minimum,
  maximum,
  exclusiveMinimum,
  exclusiveMaximum,
) => {
  if (minimum !== undefined) {
    validator = validator.min(minimum);
  }
  if (maximum !== undefined) {
    validator = validator.max(maximum);
  }
  if (exclusiveMinimum !== undefined) {
    validator = validator.min(exclusiveMinimum);
  }
  if (exclusiveMaximum !== undefined) {
    validator = validator.max(exclusiveMaximum);
  }
  return validator;
};

const applyArrayConstraints = (validator, itemSchema, minItems, maxItems) => {
  if (itemSchema) {
    validator = validator.of(itemSchema);
  }
  if (minItems !== undefined) {
    validator = validator.min(minItems);
  }
  if (maxItems !== undefined) {
    validator = validator.max(maxItems);
  }
  return validator;
};

// Generate a Yup validator from a JSON schema object
export const getValidator = (option) => {
  let validator;

  validator = getTypeValidator(option.type);
  if (option.type === "array" && option.items) {
    const itemValidator = getValidator(option.items);
    validator = applyArrayConstraints(
      validator,
      itemValidator,
      option.minItems,
      option.maxItems,
    );
  }
  validator = applyEnum(validator, option.enum);
  validator = applyMinMax(
    validator,
    option.minimum,
    option.maximum,
    option.exclusiveMinimum,
    option.exclusiveMaximum,
  );
  validator = applyRequired(validator, option.required);

  return validator;
};

// Format the model schema to include the subforms
export const formattedModel = async (schema) => {
  const subforms = {};
  const required = schema.required || [];

  await Promise.all(
    Object.keys(schema.properties)
      .filter((key) => {
        return (
          schema.properties[key].type === "object" &&
          schema.properties[key].parent
        );
      })
      .map(async (key) => {
        const obj = schema.properties[key];

        const subform = await getComponents({
          model: obj.placeholder.component,
        });

        subforms[key] = {
          properties: {
            component: obj.parent,
            params: {
              comp: {
                component: obj.placeholder.component,
                params: await formattedModel(subform.schema),
              },
            },
          },
          type: "object",
          description: obj.description,
          title: obj.title,
          parent: obj.parent,
        };
      }),
  );

  const formattedSchema = { ...schema.properties, ...subforms };

  // Add required property to each key-value pair in the formattedSchema object
  Object.keys(formattedSchema).forEach((key) => {
    formattedSchema[key] = {
      ...formattedSchema[key],
      required: required.includes(key),
    };
  });

  return formattedSchema;
};

// Format the subform schema to include the parent model
export const formattedSubform = ({ parent, model, params }) => ({
  properties: {
    component: parent,
    params: {
      comp: {
        component: model,
        params,
      },
    },
  },
});

export const checkIfHaveOptimazers = (values) => {
  if (!values) return false;

  for (const key of Object.keys(values)) {
    const param = values[key];
    if (!param || typeof param !== "object") continue;

    if (param.optimize) {
      return true;
    }

    // Only return true if a recursive check finds something
    if (checkIfHaveOptimazers(param)) {
      return true;
    }
  }

  return false;
};

export const checkHowManyOptimazers = (values) => {
  let count = 0;

  if (!values) return count;

  for (const key of Object.keys(values)) {
    const param = values[key];
    if (!param || typeof param !== "object") continue;

    if (param.optimize) {
      count += 1;
    }

    // Recursively count optimizers in nested objects
    count += checkHowManyOptimazers(param);
  }

  return count;
};

export const getParamsFromSubform = (subform) => {
  if (!subform) {
    return null;
  }
  if (subform.properties?.params?.comp?.params) {
    return subform.properties.params.comp.params;
  }
  if (subform.params !== undefined) {
    return subform.params;
  }
  return subform.properties?.params ?? null;
};

export const getModelFromSubform = (subform) => {
  if (!subform) {
    return null;
  }
  if (subform.component !== undefined) {
    return subform.component;
  }
  if (subform.properties?.params?.comp?.component) {
    return subform.properties.params.comp.component;
  }
  return subform.properties?.component ?? null;
};
