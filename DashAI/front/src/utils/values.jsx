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
