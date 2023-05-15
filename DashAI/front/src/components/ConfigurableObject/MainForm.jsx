import React from "react";
import PropTypes from "prop-types";
import { Button } from "@mui/material";
import { useFormik } from "formik";
import { FormRenderer } from "./FormRenderer";

function MainForm({
  parameterSchema,
  defaultValues,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
  formSubmitRef,
}) {
  const formik = useFormik({
    initialValues: defaultValues ?? {},
    //   validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });

  // Updates the formSubmitRef with the current formik object if formSubmitRef is not null
  // this is used when the form needs to be submitted from outside the ParameterForm component
  React.useEffect(() => {
    if (formSubmitRef !== null) {
      formSubmitRef.current = formik;
    }
  }, [formSubmitRef, formik]);

  React.useEffect(() => {
    // get current values of an input
    if (getValues !== null && typeof getValues !== "undefined") {
      getValues[1](formik.values[getValues[0]]);
    }
  }, [formik.values]);
  return (
    <div>
      {FormRenderer("", parameterSchema, formik, defaultValues)}
      {extraOptions}
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
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
};

MainForm.defaultProps = {
  defaultValues: { emptyDefaultValues: true },
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
  getValues: null,
  formSubmitRef: null,
};

export default MainForm;
