import * as Yup from "yup";

/**
 * Generates Yup validation based on the validation rules (e.g minimum, maximum) on the JSON that describes the configurable object
 * @param {object>} yupInitialObj - The initial Yup object schema (containing type validation).
 * @param {object} schema - The schema object containing validation rules.
 * @returns {object>} The modified Yup object schema.
 */
export function genYupValidation(yupInitialObj, schema) {
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
  if ("optional" in schema) {
    return finalObj;
  }
  return finalObj.required("Required");
}

/**
 * Generates a validation schema for a configurable object using its json schema.
 * initially identifies the type of each parameter for type validation
 * then it callls genYupValidation function to handle more specific validation of each parameter
 * @param {object} parameterJsonSchema the JSON that describes the configurable object
 * @returns {object} The Yup validation schema for the configurable object.
 */
export function getValidation(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  const validationObject = {};
  if (typeof properties !== "undefined") {
    const parameters = Object.keys(properties);
    parameters.forEach((param) => {
      const subSchema = properties[param].oneOf[0];
      let yupInitialObj = null;
      switch (subSchema.type) {
        case "integer":
          yupInitialObj = Yup.number().integer();
          break;
        case "number":
          yupInitialObj = Yup.number();
          break;
        case "float":
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
        validationObject[param] = genYupValidation(yupInitialObj, subSchema);
      }
    });
  }
  return Yup.object().shape(validationObject);
}
