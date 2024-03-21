import { Box, Button } from "@mui/material";
import { useFormik } from "formik";
import PropTypes from "prop-types";
import React, { useCallback, useEffect } from "react";
import { useModelSchemaStore } from "../../contexts/schema";
import useModelSchema from "../../hooks/useModelSchema";
import BoxWithTitle from "./BoxWithTitle";
import ModelSchemaFields from "./ModelSchemaFields";
import ModelSchemaSubform from "./ModelSchemaSubform";
import ModalSchemaFieldsWithOptions from "./ModelSchemaFieldsWithOptions";
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
function ModelSchemaForm({
  model,
  extraOptions,
  initialValues,
  onFormSubmit,
  onCancel,
}) {
  // manages and submits the values of the parameters in the form

  const { modelSchema, defaultValues, yupSchema, loading } = useModelSchema({
    modelName: model,
  });

  const { formValues, handleUpdateValues, properties } = useModelSchemaStore();

  const formik = useFormik({
    initialValues:
      initialValues && Object.keys(initialValues).length > 0
        ? initialValues
        : defaultValues,
    enableReinitialize: true,
    validationSchema: yupSchema,
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name) => (value) => {
      if (properties.length === 0) {
        handleUpdateValues({ ...formValues, [name]: value });
      }
      formik.setFieldValue(name, value);
    };

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;

      if ("anyOf" in fieldSchema) {
        fields.push(
          <ModalSchemaFieldsWithOptions
            title={fieldSchema.title}
            options={fieldSchema.anyOf}
            name={objName}
            field={{
              value: formik.values[objName],
              onChange: onChange(objName),
              error: formik.errors[objName],
            }}
          />,
        );
      } else if (fieldSchema.type === "object") {
        fields.push(
          <ModelSchemaSubform
            name={objName}
            label={fieldSchema.title}
            description={fieldSchema.description}
          />,
        );
      } else {
        fields.push(
          <ModelSchemaFields
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

  useEffect(() => {
    if (
      Object.keys(formValues).length === 0 &&
      (Object.keys(initialValues).length > 0 ||
        Object.keys(defaultValues).length > 0)
    ) {
      handleUpdateValues(
        initialValues && Object.keys(initialValues).length > 0
          ? initialValues
          : defaultValues,
      );
    }
  }, [formValues, initialValues, defaultValues]);

  return (
    <>
      <BoxWithTitle title="Paramenters">
        <Box
          sx={{
            height: 500,
            overflowY: "auto",
            px: 2,
            py: 4,
          }}
        >
          {loading ? <>loading..</> : renderFields()}
        </Box>
      </BoxWithTitle>
      {/* Renders additional behavior if extraOptions is not null */}
      {extraOptions}
      {/* renders a submit button if submitButton is true */}
      <Box display="flex" sx={{ width: "100%", p: 2 }} gap={2}>
        <Button variant="outlined" onClick={onCancel} fullWidth>
          Back
        </Button>
        <Button variant="contained" onClick={formik.handleSubmit} fullWidth>
          Save
        </Button>
      </Box>
    </>
  );
}

ModelSchemaForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  model: PropTypes.string.isRequired,
  initialValues: PropTypes.objectOf(
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
  onCancel: PropTypes.func,
  getValues: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  ),
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
};

export default ModelSchemaForm;
