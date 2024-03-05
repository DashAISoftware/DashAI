import * as Yup from "yup";

export const generateYupSchema = (schemaObj) => {
  const schema = {};
  const initialValues = {};

  // Iterate over the properties of the schema object
  Object.keys(schemaObj).forEach((key) => {
    const subSchema = schemaObj[key];

    if (subSchema.type === "object") {
      const { yupSubSchema, initialSubValues } = generateObjectSchema(
        subSchema.properties,
      );
      schema[key] = Yup.object().shape(yupSubSchema);
      initialValues[key] = initialSubValues;
    } else {
      const field = generateField(subSchema);
      schema[key] = field.schema;
      initialValues[key] = field.initialValue;
    }
  });

  return { schema: Yup.object().shape(schema), initialValues };
};

const generateObjectSchema = (subSchema) => {
  const yupSubSchema = {};
  const initialSubValues = {};

  // Create a Yup schema for each sub-schema property
  Object.keys(subSchema).forEach((subKey) => {
    const subField = subSchema[subKey];
    const field = generateField(subField);

    yupSubSchema[subKey] = field.schema;
    initialSubValues[subKey] = field.initialValue;
  });

  return { yupSubSchema, initialSubValues };
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

// function applyEnum(validator, enumValues) {
//   if (enumValues) {
//     return validator.oneOf(enumValues);
//   }
//   return validator;
// }

// function applyMinMax(validator, minimum, maximum) {
//   if (minimum !== undefined) {
//     validator = validator.min(minimum);
//   }
//   if (maximum !== undefined) {
//     validator = validator.max(maximum);
//   }
//   return validator;
// }

// export function getValidator(option) {
//   let validator;

//   if (option.anyOf) {
//     const validators = option.anyOf.map((subOption) => {
//       let subValidator = getTypeValidator(subOption.type);
//       subValidator = applyEnum(subValidator, subOption.enum);
//       subValidator = applyMinMax(
//         subValidator,
//         subOption.minimum,
//         subOption.maximum,
//       );
//       return subValidator;
//     });

//     validator = yup.mixed().nullable().oneOf(validators);
//   } else {
//     validator = getTypeValidator(option.type);
//     validator = applyEnum(validator, option.enum);
//     validator = applyMinMax(validator, option.minimum, option.maximum);
//   }

//   return validator;
// }

// export async function createPropertySchema(property, key) {
//   let propertySchema = getValidator(property);

//   if (property.enum) {
//     propertySchema = propertySchema.oneOf(property.enum);
//   }

//   if (property.minimum !== undefined) {
//     propertySchema = propertySchema.min(property.minimum);
//   }

//   //   if (property.subform) {
//   //     const subformProperties = await fetchPropertiesForSubform(property.subform);
//   //     const subformSchema = await createSchema(subformProperties, key);
//   //     propertySchema = propertySchema.shape(subformSchema);
//   //   }

//   return propertySchema;
// }

// export async function createSchema(schemaObject) {
//   const propertySchemas = await Promise.all(
//     Object.entries(schemaObject.properties).map(async ([key, value]) => {
//       let propertySchema = await createPropertySchema(value, key);
//       if (schemaObject.required && schemaObject.required.includes(key)) {
//         propertySchema = propertySchema.required();
//       }

//       return [key, propertySchema, value.default]; // Include default value in the result
//     }),
//   );

//   return yup.object().shape(Object.fromEntries(propertySchemas));
// }

// export const generateYupSchema = (schemaObj) => {
//   const schema = {};
//   const initialValues = {};

//   // Iterate over the properties of the schema object
//   Object.keys(schemaObj).forEach((key) => {
//     const subSchema = schemaObj[key];

//     // Create a Yup schema for each sub-schema
//     const subSchemaKeys = Object.keys(subSchema);
//     const yupSubSchema = {};
//     const initialSubValues = {};
//     subSchemaKeys.forEach((subKey) => {
//       const subField = subSchema[subKey];
//       let field = yup;
//       switch (subField.type) {
//         case "string":
//           field = field.string().label(subField.title);
//           if (subField.enum) {
//             field = field.oneOf(subField.enum).label(subField.title);
//           }
//           break;
//         case "number":
//           field = field.number().label(subField.title);
//           if (subField.minimum !== undefined) {
//             field = field.min(
//               subField.minimum,
//               `Must be greater than or equal to ${subField.minimum}`,
//             );
//           }
//           if (subField.maximum !== undefined) {
//             field = field.max(
//               subField.maximum,
//               `Must be less than or equal to ${subField.maximum}`,
//             );
//           }
//           break;
//         case "integer":
//           field = field.number().integer().label(subField.title);
//           if (subField.minimum !== undefined) {
//             field = field.min(
//               subField.minimum,
//               `Must be greater than or equal to ${subField.minimum}`,
//             );
//           }
//           if (subField.maximum !== undefined) {
//             field = field.max(
//               subField.maximum,
//               `Must be less than or equal to ${subField.maximum}`,
//             );
//           }
//           break;
//         case "boolean":
//           field = field.boolean().label(subField.title);
//           break;
//         default:
//           break;
//       }
//       yupSubSchema[subKey] = field;

//       // Generate initial values based on the placeholder value
//       if (subField.placeholder !== undefined) {
//         initialSubValues[subKey] = subField.placeholder;
//       }
//     });

//     // Add the sub-schema to the main schema
//     schema[key] = yup.object().shape(yupSubSchema);
//     initialValues[key] = initialSubValues;
//   });

//   console.log("Generated Yup Schema:", schema);

//   return { schema: yup.object().shape(schema), initialValues };
// };
