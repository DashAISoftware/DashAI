import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { FormRenderer } from "./FormRenderer";
import { useFormik } from "formik";
import { getValidation } from "./validation";
/**
 * This component renders a subform, used for recursive parameters.
 * This subform is also a parameter of the parent/main form.
 * The value of this parameter is an object that contains the values of all parameters in the subform.
 * Since this is also a parameter, it uses a Formik function to update its own values.
 * @param {object} name name of the configurable object
 * @param {object} parameterSchema JSON object that describes a configurable object
 * @param {function} setFieldValue formik function to change the values of a parameter given its name
 * @param {string} choice value of the selected option to render as subform in ClassInput
 * @param {object} defaultValues default values of the parameters of the configurable object
 */
function Subform({
  name,
  parameterSchema,
  setFieldValue,
  choice,
  defaultValues,
}) {
  // adds "choice", the selected configurable object to render as a subform, to the values of the form
  const newDefaultValues = { ...defaultValues, choice };

  // manages the values of the parameters in the form
  const formik = useFormik({
    initialValues: newDefaultValues,
    validationSchema: getValidation(parameterSchema),
  });

  // updates the values of this form in the main/parent form
  useEffect(() => {
    setFieldValue(name, formik.values);
  }, [formik.values]);

  return (
    <div key={`parameterForm-${choice}`}>
      {FormRenderer(name, parameterSchema, formik, defaultValues)}
    </div>
  );
}
Subform.propTypes = {
  name: PropTypes.string,
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
  setFieldValue: PropTypes.func.isRequired,
  choice: PropTypes.string.isRequired,
  defaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
      PropTypes.bool,
      PropTypes.object,
    ]),
  ),
};
Subform.defaultProps = {
  name: "undefined",
  defaultValues: { emptyDefaultValues: true },
};

export default Subform;
