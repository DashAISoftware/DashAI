import * as Yup from "yup";

/**
 * Generates Yup validation based on the validation rules (e.g minimum, maximum) on the JSON that describes the configurable object
 * @param {object} yupInitialObj - The initial Yup object schema (containing type validation).
 * @param {object} schema - The schema object containing validation rules.
 * @returns {object} The modified Yup object schema.
 */

export function getTypeString(type, objName) {
  if (Array.isArray(type)) {
    if (type.length > 2) {
      throw new Error(
        `An error occurred while rendering ${objName}. The array type can have at most two elements, but it has ${type.length} elements.`,
      );
    }

    const filteredArray = type.filter((item) => item !== "null");

    if (filteredArray.length > 1) {
      throw new Error(
        `An error occurred while rendering ${objName}. The array type can have at most one non-null element, but it has ${filteredArray.length} non-null elements.`,
      );
    }

    return {
      typeStr: filteredArray[0] || null,
      nullable: type.includes("null"),
    };
  } else if (typeof type === "string") {
    return {
      typeStr: type,
      nullable: false,
    };
  } else {
    throw new Error(
      `An error occurred while rendering ${objName}. The type value (${type}) must be of type array or string, but the provided type is ${typeof type}.`,
    );
  }
}

export function genYupValidation(yupInitialObj, schema, nullable) {
  let finalObj = yupInitialObj;
  if ("maximum" in schema) {
    finalObj = finalObj.max(schema.maximum, schema.error_msg);
  }
  if ("minimum" in schema) {
    finalObj = finalObj.min(schema.minimum, schema.error_msg);
  }
  if ("exclusiveMinimum" in schema) {
    finalObj = finalObj.min(
      Math.min(schema.exclusiveMinimum, schema.default),
      schema.error_msg,
    );
  }
  if ("enum" in schema) {
    finalObj = finalObj.oneOf(schema.enum);
  }
  if (nullable) {
    return finalObj.nullable(true);
  }
  return finalObj.required("Required");
}

/**
 * Generates a validation schema for a configurable object using its json schema.
 * initially identifies the type of each parameter for type validation
 * then it calls genYupValidation function to handle more specific validation of each parameter
 * @param {object} parameterJsonSchema the JSON that describes the configurable object
 * @returns {object} The Yup validation schema for the configurable object.
 */
export function getValidationSchema(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  const validationObject = {};

  if (typeof properties !== "undefined") {
    const parameters = Object.keys(properties);
    parameters.forEach((param) => {
      const subSchema = properties[param].oneOf[0];
      const { typeStr, nullable } = getTypeString(subSchema.type, "");
      let yupInitialObj = null;
      switch (typeStr) {
        case "integer":
          yupInitialObj = Yup.number().integer();
          break;
        case "number":
          yupInitialObj = Yup.number();
          break;
        case "string":
          yupInitialObj = Yup.string();
          break;
        case "text":
          yupInitialObj = Yup.string();
          break;
        case "boolean":
          yupInitialObj = Yup.boolean();
          break;
        default:
          yupInitialObj = "none";
      }
      if (yupInitialObj !== "none") {
        validationObject[param] = genYupValidation(
          yupInitialObj,
          subSchema,
          nullable,
        );
      }
    });
  }
  return Yup.object().shape(validationObject);
}
