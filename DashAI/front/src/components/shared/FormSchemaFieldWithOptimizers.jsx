import PropTypes from "prop-types";
import React from "react";
import OptimizeIntegerInput from "../configurableObject/Inputs/IntegerInputOptimize";
import OptimizeNumberInput from "../configurableObject/Inputs/NumberInputOptimize";

/**
 * This function takes JSON object that describes a configurable object
 * and dynamically generates a form by mapping the type of each parameter
 * to the corresponding Input component defined in the Inputs folder.
 * @param {string} objName name of the configurable object
 * @param {object} paramJsonSchema the json object to map into an input
 * @param {object} field object that contains the value of the parameter and a function to set the value
 * @param {string} error error message to display
 *
 */
function FormSchemaFieldWithOptimizers({
  objName,
  paramJsonSchema,
  field,
  setError,
  error,
}) {
  const { type } = paramJsonSchema;

  const handleSetError = (error) => {
    setErrorField(error);
    setError && setError(Boolean(error));
  };

  const optimize = paramJsonSchema?.placeholder?.optimize;

  const onChange = (value) => {};

  // Props that are common to almost all form inputs

  const commonProps = {
    name: objName,
    value: field?.value,
    label: paramJsonSchema.title,
    onChange: field?.onChange,
    error: field?.error || error || undefined,
    description: paramJsonSchema?.description,
  };

  if (!objName) {
    return null;
  }

  switch (type) {
    case "integer":
      return (
        <OptimizeIntegerInput
          {...commonProps}
          placeholder={paramJsonSchema.placeholder}
        />
      );
    case "object":
      return (
        <OptimizeNumberInput
          {...commonProps}
          placeholder={paramJsonSchema.placeholder}
        />
      );
  }
}

FormSchemaFieldWithOptimizers.propTypes = {
  objName: PropTypes.string,
  paramJsonSchema: PropTypes.object,
  field: PropTypes.object,
  error: PropTypes.string,
};

export default FormSchemaFieldWithOptimizers;
