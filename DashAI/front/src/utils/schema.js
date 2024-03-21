import * as Yup from "yup";

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
  } else {
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
  }

  return initialValues;
};

const generateField = (subSchema) => {
  let field;

  if (subSchema.anyOf) {
    field = Yup.mixed().nullable();
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

const applyEnum = (validator, enumValues) => {
  if (enumValues) {
    return validator.oneOf(enumValues);
  }
  return validator;
};

const applyMinMax = (validator, minimum, maximum) => {
  if (minimum !== undefined) {
    validator = validator.min(minimum);
  }
  if (maximum !== undefined) {
    validator = validator.max(maximum);
  }
  return validator;
};

const getValidator = (option) => {
  let validator;

  validator = getTypeValidator(option.type);
  validator = applyEnum(validator, option.enum);
  validator = applyMinMax(validator, option.minimum, option.maximum);

  return validator;
};

// "obj": {
//   "component": "DummyParamComponent",
//   "params": {
//       "comp": {"component": "DummyComponent", "params": {"integer": 1}}
//   },
// },
