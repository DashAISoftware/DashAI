import * as Yup from "yup";

export const generateYupSchema = (schemaObj) => {
  const schema = {};
  const initialValues = {};

  // Iterate over the properties of the schema object
  Object.keys(schemaObj).forEach((key) => {
    const subSchema = schemaObj[key];
    const field = generateField(subSchema);
    schema[key] = field.schema;
    if (subSchema.type === "object") {
      const { initialSubValues } = generateInitialValues(
        subSchema.properties.params.comp.params,
      );
      initialValues[key] = {
        properties: {
          component: subSchema.properties.component,
          params: {
            comp: {
              component: subSchema.properties.params.comp.component,
              params: initialSubValues,
            },
          },
        },
      };
    } else {
      initialValues[key] = field.initialValue;
    }
  });

  return { schema: Yup.object().shape(schema), initialValues };
};

const generateInitialValues = (subSchema) => {
  const initialSubValues = {};

  // Create a Yup schema for each sub-schema property
  Object.keys(subSchema).forEach((subKey) => {
    const subField = subSchema[subKey];
    const field = generateField(subField);

    initialSubValues[subKey] = field.initialValue;
  });

  return { initialSubValues };
};
const generateField = (subSchema) => {
  let field;
  let initialValue;

  if (subSchema.anyOf) {
    const validators = subSchema.anyOf.map((option) => getValidator(option));
    field = Yup.mixed().nullable().oneOf(validators);
    initialValue = subSchema.anyOf.find(
      (option) => option.placeholder !== undefined,
    )?.placeholder;
  } else {
    field = getValidator(subSchema);
    initialValue = subSchema.placeholder;
  }

  return { schema: field, initialValue };
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
