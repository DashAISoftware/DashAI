import React, { useState, useEffect } from "react";
import MainForm from "./MainForm";
import PropTypes from "prop-types";
import { getFullDefaultValues } from "../../api/values";
/**
 * To render a parameter form, simply import and use this component.
 * It encapsulates all the necessary logic defined within the ConfigurableObject folder components,
 * making it the only component needed for this purpose.
 * The simplest way to use this component is: <ParameterForm parameterSchema={schema} />
 * @param {object} parameterSchema JSON object that describes a configurable object
 * @param {object} initialValues default values for the form to render
 * @param {object} extraOptions a component of code that includes additional behavior to the form
 * @param {bool} submitButton true to render a submit button, false to not.
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * The function should be defined as follows: (values) => {...}
 * @param {Array} getValues array [name_of_parameter, function] the function is called when the parameter changes
 * to include additional behavior to the form e.g showing more parameters depending on a boolean value.
 */
function ParameterForm({
  parameterSchema,
  initialValues,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
  formSubmitRef,
}) {
  const [defaultValues, setDefaultValues] = useState(initialValues);
  const [loading, setLoading] = useState(initialValues === null);

  // checks if the default values correspond to the parameterSchema
  // TODO: find a better way because this fails if the new parameterSchema has a parameter with the same name as the previous parameterSchema.
  const checkDefaultValues = () => {
    if (defaultValues === null) {
      return false;
    }
    return Object.keys(parameterSchema.properties)[0] in defaultValues;
  };

  const getFormInitialValues = async () => {
    setLoading(true);
    try {
      const values = await getFullDefaultValues(parameterSchema);
      setDefaultValues(values);
    } catch (error) {
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unkown Error", error.message);
      }
    } finally {
      setLoading(false);
    }
  };

  // gets the initial values of the form if they aren't passed as a prop
  useEffect(() => {
    if (initialValues === null) {
      getFormInitialValues();
    }
  }, [parameterSchema]);

  // stops the render if the defaultValues are not ready
  if (loading || !checkDefaultValues()) {
    return <React.Fragment />;
  } else {
    return (
      <MainForm
        parameterSchema={parameterSchema}
        defaultValues={defaultValues}
        onFormSubmit={onFormSubmit}
        extraOptions={extraOptions}
        submitButton={submitButton}
        getValues={getValues}
        formSubmitRef={formSubmitRef}
      />
    );
  }
}

ParameterForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
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
  getValues: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  ),
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
};
ParameterForm.defaultProps = {
  initialValues: null,
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
  getValues: null,
  formSubmitRef: null,
};
export default ParameterForm;
