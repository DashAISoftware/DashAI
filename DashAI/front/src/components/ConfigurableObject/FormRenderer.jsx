import React from "react";
import { Stack } from "@mui/material";
import ClassInput from "./Inputs/ClassInput";
import IntegerInput from "./Inputs/IntegerInput";
import NumberInput from "./Inputs/NumberInput";
import SelectInput from "./Inputs/SelectInput";
import TextInput from "./Inputs/TextInput";
import BooleanInput from "./Inputs/BooleanInput";
import FloatInput from "./Inputs/FloatInput";

export function FormRenderer(objName, paramJsonSchema, formik, defaultValues) {
  const { type, properties } = paramJsonSchema;
  // Props that are common to almost all form inputs.
  const commonProps = {
    name: objName,
    value: formik.values[objName],
    onChange: formik.handleChange,
    error: formik.errors[objName],
    description: paramJsonSchema.description,
    key: objName,
  };
  switch (type) {
    case "object":
      return (
        <Stack key={objName} spacing={3}>
          {Object.keys(properties).map((parameter) =>
            FormRenderer(
              parameter,
              properties[parameter].oneOf[0],
              formik,
              defaultValues[parameter]
            )
          )}
        </Stack>
      );
    case "class":
      return (
        <ClassInput
          name={objName}
          paramJsonSchema={paramJsonSchema}
          setFieldValue={formik.setFieldValue}
          formDefaultValues={defaultValues}
          key={`rec-param-${objName}`}
        />
      );
    case "integer":
      return <IntegerInput {...commonProps} />;
    case "number":
      return <NumberInput {...commonProps} />;
    case "string":
      return <SelectInput {...commonProps} options={paramJsonSchema.enum} />;
    case "text":
      return <TextInput {...commonProps} />;
    case "boolean":
      return <BooleanInput {...commonProps} />;
    case "float":
      return <FloatInput {...commonProps} />;
    default:
      throw new Error(
        `Error while rendering ${objName}: ${type} is not a valid parameter type.`
      );
  }
}
