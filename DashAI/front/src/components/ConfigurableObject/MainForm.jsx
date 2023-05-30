import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { Button } from "@mui/material";
import { useFormik } from "formik";
import { FormRenderer } from "./FormRenderer";
import { getValidation } from "./validation";
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
function MainForm({
  parameterSchema,
  defaultValues,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
}) {
  // manages and submits the values of the parameters in the form
  const formik = useFormik({
    initialValues: defaultValues ?? {},
    validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });

  // triggers a function with the current value of an input to include additional behavior in the form
  useEffect(() => {
    if (getValues !== null && typeof getValues !== "undefined") {
      getValues[1](formik.values[getValues[0]]);
    }
  }, [formik.values]);

  return (
    <div>
      {/* Renders the form */}
      {FormRenderer("", parameterSchema, formik, defaultValues)}

      {/* Renders additional behavior if extraOptions is not null */}
      {extraOptions}

      {/* renders a submit button if submitButton is true */}
      {submitButton && (
        <Button
          style={{ float: "right" }}
          size="large"
          onClick={formik.handleSubmit}
        >
          Save
        </Button>
      )}
    </div>
  );
}

MainForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object]),
  ).isRequired,
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
};

MainForm.defaultProps = {
  defaultValues: { emptyDefaultValues: true },
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
  getValues: null,
};

export default MainForm;
