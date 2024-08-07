import React from "react";
import BooleanInput from "../configurableObject/Inputs/BooleanInput";
import IntegerInput from "../configurableObject/Inputs/IntegerInput";
import NumberInput from "../configurableObject/Inputs/NumberInput";
import SelectInput from "../configurableObject/Inputs/SelectInput";
import TextInput from "../configurableObject/Inputs/TextInput";
import OptimizeIntegerInput from "../configurableObject/Inputs/IntegerInputOptimize";
import OptimizeNumberInput from "../configurableObject/Inputs/NumberInputOptimize";
import PropTypes from "prop-types";

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
function FormSchemaField({ objName, paramJsonSchema, field, error }) {
  const { type } = paramJsonSchema;

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
      return <IntegerInput {...commonProps} />;
    case "number":
      return <NumberInput {...commonProps} />;
    case "string":
      if (paramJsonSchema.enum) {
        return (
          <SelectInput
            {...commonProps}
            options={paramJsonSchema.enum}
            optionNames={paramJsonSchema.enumNames}
          />
        );
      } else {
        return <TextInput {...commonProps} />;
      }
    case "text":
      return <TextInput {...commonProps} />;
    case "boolean":
      return <BooleanInput {...commonProps} />;
    case "null" || "undefined":
      return <TextInput {...commonProps} disabled />;
    default:
      return null;
  }
}

FormSchemaField.propTypes = {
  objName: PropTypes.string,
  paramJsonSchema: PropTypes.object,
  field: PropTypes.object,
  error: PropTypes.string,
};

export default FormSchemaField;
