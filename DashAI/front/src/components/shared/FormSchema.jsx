import PropTypes from "prop-types";
import { Box } from "@mui/material";
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
 * @param {function} onValuesChange function to call when the form values change
 * @param {bool} showBorder if true, the parameter container will have a border
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
  saveButtonText,
  onValuesChange,
  showBorder = true,
  hideButtons = false,
  excludeFields = [],
}) {
  const { formik, modelSchema, loading, handleUpdateSchema } = useFormSchema({
    model,
    initialValues,
    formSubmitRef,
    setError,
    onValuesChange,
  });

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        minHeight: 0,
      }}
    >
      <FormSchemaParameterContainer showBorder={showBorder}>
        <FormSchemaRenderFields
          modelSchema={modelSchema}
          formik={formik}
          autoSave={autoSave}
          handleUpdateSchema={handleUpdateSchema}
          onFormSubmit={onFormSubmit}
          setError={setError}
          errorsMessage={errorsMessage}
          excludeFields={excludeFields}
        />
      </FormSchemaParameterContainer>

      {!hideButtons && (
        <FormSchemaButtonGroup
          onCancel={onCancel}
          onFormSubmit={onFormSubmit}
          autoSave={autoSave}
          formik={formik}
          error={error}
          saveButtonText={saveButtonText}
        />
      )}
    </Box>
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
  saveButtonText: PropTypes.string,
  onValuesChange: PropTypes.func,
  showBorder: PropTypes.bool,
  hideButtons: PropTypes.bool,
  excludeFields: PropTypes.arrayOf(PropTypes.string),
};

export default FormSchema;
