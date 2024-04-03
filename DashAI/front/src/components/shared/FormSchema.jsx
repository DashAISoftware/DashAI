import { Button, ButtonGroup } from "@mui/material";
import { useFormik } from "formik";
import PropTypes from "prop-types";
import React, { useCallback, useEffect } from "react";
import { useFormSchemaStore } from "../../contexts/schema";
import useFormSchema from "../../hooks/useFormSchema";
import FormSchemaFields from "./FormSchemaFields";
import ModalSchemaFieldsWithOptions from "./FormSchemaFieldsWithOptions";
import FormSchemaFormParameterContainer from "./FormSchemaFormParameterContainer";
import FormSchemaSubform from "./FormSchemaSubform";
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
function FormSchema({
  model,
  onFormSubmit,
  onCancel,
  extraOptions,
  initialValues,
}) {
  // manages and submits the values of the parameters in the form

  const { modelSchema, defaultValues, yupSchema, loading } = useFormSchema({
    modelName: model,
  });

  const { formValues, handleUpdateSchema } = useFormSchemaStore();

  const formik = useFormik({
    initialValues:
      initialValues && Object.keys(initialValues).length > 0
        ? initialValues
        : defaultValues,
    enableReinitialize: true,
    validationSchema: yupSchema,
  });

  const renderFields = useCallback(() => {
    const fields = [];

    const onChange = (name) => (value) => {
      handleUpdateSchema({ [name]: value });
      formik.setFieldValue(name, value);
    };

    for (const key in modelSchema) {
      const fieldSchema = modelSchema[key];
      const objName = key;

      if ("anyOf" in fieldSchema) {
        fields.push(
          <ModalSchemaFieldsWithOptions
            title={fieldSchema.title}
            description={fieldSchema.description}
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
          <FormSchemaSubform
            name={objName}
            label={fieldSchema.title}
            description={fieldSchema.description}
          />,
        );
      } else {
        fields.push(
          <FormSchemaFields
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

  // for initialiaze the form with the default values if the form is empty

  useEffect(() => {
    if (
      Object.keys(formValues).length === 0 &&
      (Object.keys(initialValues).length > 0 ||
        Object.keys(defaultValues).length > 0)
    ) {
      handleUpdateSchema(
        initialValues && Object.keys(initialValues).length > 0
          ? initialValues
          : defaultValues,
      );
    }
  }, [formValues, initialValues, defaultValues]);

  return (
    <>
      <FormSchemaFormParameterContainer>
        {loading ? <>loading..</> : renderFields()}{" "}
      </FormSchemaFormParameterContainer>
      {/* Renders additional behavior if extraOptions is not null */}
      {extraOptions}
      {/* renders a submit button if submitButton is true */}
      <ButtonGroup size="large" sx={{ justifyContent: "flex-end" }}>
        <Button variant="outlined" onClick={onCancel}>
          Back
        </Button>
        <Button variant="contained" onClick={onFormSubmit}>
          Save
        </Button>
      </ButtonGroup>
    </>
  );
}

FormSchema.propTypes = {
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

export default FormSchema;
