/* eslint-disable react/prop-types */
import React from "react";
import BooleanInput from "../configurableObject/Inputs/BooleanInput";
import IntegerInput from "../configurableObject/Inputs/IntegerInput";
import NumberInput from "../configurableObject/Inputs/NumberInput";
import SelectInput from "../configurableObject/Inputs/SelectInput";
import TextInput from "../configurableObject/Inputs/TextInput";
/**
 * This function takes JSON object that describes a configurable object
 * and dynamically generates a form by mapping the type of each parameter
 * to the corresponding Input component defined in the Inputs folder.
 * @param {string} objName name of the configurable object
 * @param {object} paramJsonSchema the json object to map into an input
 * @param {object} formik formik hook to manage the values of the parameter
 * @param {object} defaultValues default values of the object to map into an input
 *
 */
export function FormModelSchemaFields({ objName, paramJsonSchema, field }) {
  const { type } = paramJsonSchema;

  // Props that are common to almost all form inputs

  const commonProps = {
    name: objName,
    value: field?.value,
    onChange: field?.onChange,
    setFieldValue: field?.setFieldValue,
    error: field?.error,
    description: paramJsonSchema?.description,
    key: objName,
  };

  switch (type) {
    case "object":
      return null;
    //   return (
    //     <ClassInput
    //       name={objName}
    //       properties={properties}
    //       setFieldValue={formik.setFieldValue}
    //       key={`rec-param-${objName}`}
    //     />
    //   );
    case "integer":
      return <IntegerInput {...commonProps} />;
    case "number":
      return <NumberInput {...commonProps} />;
    case "string":
      return (
        <SelectInput
          {...commonProps}
          options={paramJsonSchema.enum}
          optionNames={paramJsonSchema.enumNames}
        />
      );
    case "text":
      return <TextInput {...commonProps} />;
    case "boolean":
      return <BooleanInput {...commonProps} />;
    default:
      return null;
  }
}
