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
  choice = "none"
) {
  const { properties } = parameterJsonSchema;

  if (!properties || Object.keys(properties).length === 0) {
    return {};
  }

  const defaultValues = choice === "none" ? {} : { choice };

  for (const param of Object.keys(properties)) {
    const val = properties[param].oneOf[0].default;

    if (val !== undefined) {
      defaultValues[param] = val;
    } else {
      const { parent } = properties[param].oneOf[0];
      let fetchedOptions;
      let parameterSchema;

      try {
        fetchedOptions = await fetch(
          `${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parent}`
        );
        const receivedOptions = await fetchedOptions.json();
        const [first] = receivedOptions;

        parameterSchema = await fetch(
          `${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + first}`
        ).then((res) => res.json());

        defaultValues[param] = await getFullDefaultValues(
          parameterSchema,
          first
        );
      } catch (error) {
        console.error(error);
      }
    }
  }

  return defaultValues;
}
