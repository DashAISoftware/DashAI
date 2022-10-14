export function getDefaultValues(parameterJsonSchema) {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    const defaultValues = {};
    parameters.forEach((param) => {
      const val = properties[param].oneOf[0].default;
      defaultValues[param] = typeof val !== 'undefined' ? val : { choice: '' };
    });
    return (defaultValues);
  }
  return ('null');
}

export async function getFullDefaultValues(parameterJsonSchema, choice = 'none') {
  const { properties } = parameterJsonSchema;
  if (typeof properties !== 'undefined') {
    const parameters = Object.keys(properties);
    const defaultValues = choice === 'none' ? {} : { choice };
    parameters.forEach(async (param) => {
      const val = properties[param].oneOf[0].default;
      if (val !== undefined) {
        defaultValues[param] = val;
      } else {
        const { parent } = properties[param].oneOf[0];
        const fetchedOptions = await fetch(`${process.env.REACT_APP_GET_CHILDREN_ENDPOINT + parent}`);
        const receivedOptions = await fetchedOptions.json();
        const [first] = receivedOptions;
        const fetchedParams = await fetch(`${process.env.REACT_APP_SELECT_MODEL_ENDPOINT + first}`);
        const parameterSchema = await fetchedParams.json();
        defaultValues[param] = await getFullDefaultValues(parameterSchema, first);
      }
    });
    return (defaultValues);
  }
  return ({});
}
