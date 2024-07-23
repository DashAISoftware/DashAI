import PropTypes from "prop-types";
import React from "react";
import useFormSchema from "../../hooks/useFormSchema";
import FormSchemaButtonGroup from "./FormSchemaButtonGroup";
import FormSchemaParameterContainer from "./FormSchemaParameterContainer";
import FormSchemaRenderFields from "./FormSchemaRenderFields";
/**
 * This code implements a component that is responsible for rendering the main form,
 * managing the values of all the subforms, and submitting the values of the parameters.
 * It acts as a central control point for the entire form.
 * @param {string} model string that describes a configurable object
 * @param {object} initialValues default values of the parameters, obtained from parameterSchema
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * @param {bool} autoSave if true, the form will be submitted automatically when a parameter changes
 * @param {function} onCancel function to call when the cancel button is clicked
 * @param {object} formSubmitRef a reference to the formik object
 * @param {function} setError function to set an error in the form
 * @param {object} errors object that contains the errors of the form
 */
function FormSchema({
  model,
  initialValues,
  onFormSubmit,
  autoSave,
  onCancel,
  formSubmitRef,
  error,
  setError,
  errorsMessage,
}) {
  const { formik, modelSchema, loading, handleUpdateSchema } = useFormSchema({
    model,
    initialValues,
    formSubmitRef,
    setError,
  });

  return (
    <>
      <FormSchemaParameterContainer>
        <FormSchemaRenderFields
          modelSchema={modelSchema}
          formik={formik}
          autoSave={autoSave}
          handleUpdateSchema={handleUpdateSchema}
          onFormSubmit={onFormSubmit}
          setError={setError}
          errorsMessage={errorsMessage}
        />
      </FormSchemaParameterContainer>

      <FormSchemaButtonGroup
        onCancel={onCancel}
        onFormSubmit={onFormSubmit}
        autoSave={autoSave}
        formik={formik}
        error={error}
      />
    </>
  );
}

FormSchema.propTypes = {
  model: PropTypes.string,
  initialValues: PropTypes.object,
  onFormSubmit: PropTypes.func,
  autoSave: PropTypes.bool,
  onCancel: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
  setError: PropTypes.func,
  errorsMessage: PropTypes.object,
};

export default FormSchema;
