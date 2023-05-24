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
 * @param {object} extraOptions a component of code that includes additional behavior to the form
 * @param {bool} submitButton true to render a submit button, false to not.
 * @param {function} onFormSubmit  function that submits the form, receives the parameter values as a key-value object.
 * The function should be defined as follows: (values) => {...}
 * @param {Array} getValues array [name_of_parameter, function] the function is called when the parameter changes
 * to include additional behavior to the form e.g showing more parameters depending on a boolean value.
 */
function ParameterForm({
  parameterSchema,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
}) {
  const [defaultValues, setDefaultValues] = useState(null);
  const [loading, setLoading] = useState(true);

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

  // gets the initial values of the form
  useEffect(() => {
    getFormInitialValues();
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
      />
    );
  }
}

ParameterForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  onFormSubmit: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  submitButton: PropTypes.bool,
  getValues: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.func]),
  ),
};
ParameterForm.defaultProps = {
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
  getValues: null,
};
export default ParameterForm;
