import * as Yup from "yup";
import { getComponents } from "../api/component";

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

const generateInitialValues = (subSchema) => {
  let initialValues = {};
  if (subSchema.type !== "object") {
    initialValues = subSchema.placeholder;
    // case of recursive parameter
  } else if (subSchema.type === "object" && (subSchema.placeholder?.optimize!== undefined))  {
      initialValues = subSchema.placeholder;
  } else if (subSchema.parent) {
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

  if (subSchema.anyOf) {
    field = Yup.mixed().nullable();
  } else if (subSchema.type === "object") {
    field = Yup.object();

    if (!subSchema.parent && !(subSchema.placeholder?.optimize!== undefined)) {
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

const applyMinMax = (validator, minimum, maximum, exclusiveMinimum) => {
  if (minimum !== undefined) {
    validator = validator.min(minimum);
  }
  if (maximum !== undefined) {
    validator = validator.max(maximum);
  }
  if (exclusiveMinimum !== undefined) {
    validator = validator.min(exclusiveMinimum);
  }
  return validator;
};

// Generate a Yup validator from a JSON schema object
export const getValidator = (option) => {
  let validator;

  validator = getTypeValidator(option.type);
  validator = applyEnum(validator, option.enum);
  validator = applyMinMax(
    validator,
    option.minimum,
    option.maximum,
    option.exclusiveMinimum
      ? Math.min(option.exclusiveMinimum, option.default)
      : undefined,
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
