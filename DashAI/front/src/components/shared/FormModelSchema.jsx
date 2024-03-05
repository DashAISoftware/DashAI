import { Box, Button, Stack } from "@mui/material";
import { useFormik } from "formik";
import PropTypes from "prop-types";
import useModelSchema from "../../hooks/useModelSchema";
import { FormModelSchemaFields } from "./FormModelSchemaFields";
import React, { useCallback } from "react";
/**
 * This code implements a component that is responsible for rendering the main form,
 * managing the values of all the subforms, and submitting the values of the parameters.
 * It acts as a central control point for the entire form.
 * @param {object} parameterSchema JSON object that describes a configurable object
 * @param {object} defaultValues default values of the parameters, obtained from parameterSchema
 * @param {object} extraOptions a component of code that includes additional behavior to the form
 * @param {bool} submitButton true to render a submit button, false to not.
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * The function should be defined as follows: (values) => {...}
 * @param {Array} getValues array [name_of_parameter, function] the function is called when the parameter changes
 * to include additional behavior to the form e.g showing more parameters depending on a boolean value.
 */
function FormModelSchema({ model, extraOptions, submitButton, onFormSubmit }) {
  // manages and submits the values of the parameters in the form

  const { modelSchema, defaultValues, yupSchema } = useModelSchema({
    model,
  });

  const formik = useFormik({
    initialValues: defaultValues ?? {},
    enableReinitialize: true,
    validationSchema: yupSchema,
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name) => (value) => {
      formik.setFieldValue(name, value);
    };

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;

      if (fieldSchema.type === "object") {
        for (const subKey in fieldSchema.properties) {
          const subFieldSchema = fieldSchema.properties[subKey];

          fields.push(
            <FormModelSchemaFields
              objName={`${objName}.${subKey}`}
              paramJsonSchema={subFieldSchema}
              field={{
                value: formik.values[objName]?.[subKey],
                onChange: onChange(`${objName}.${subKey}`),
                error: formik.errors[objName]?.[subKey],
              }}
            />,
          );
        }
      } else {
        fields.push(
          <FormModelSchemaFields
            objName={objName}
            paramJsonSchema={fieldSchema}
            field={{
              value: formik.values[objName],
              onChange: onChange(objName),
              error: formik.errors[objName],
            }}
          />,
        );
      }
    }

    return fields;
  }, [modelSchema, formik]);

  return (
    <Stack>
      {/* Renders the form */}
      {renderFields()}

      {/* Renders additional behavior if extraOptions is not null */}
      {extraOptions}

      {/* renders a submit button if submitButton is true */}
      {submitButton && (
        <Box sx={{ width: "100%", p: 2 }}>
          <Button variant="contained" onClick={formik.handleSubmit} fullWidth>
            Save
          </Button>
        </Box>
      )}
    </Stack>
  );
}

FormModelSchema.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  model: PropTypes.string.isRequired,
  defaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ]),
  ),
  onFormSubmit: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  submitButton: PropTypes.bool,
  getValues: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  ),
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
};

export default FormModelSchema;
