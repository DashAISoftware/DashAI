import React from "react";
import PropTypes from "prop-types";
import { Button } from "@mui/material";
import { useFormik } from "formik";
import { genInput } from "./FormInputs";

function MainForm({
  parameterSchema,
  defaultValues,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
}) {
  const formik = useFormik({
    initialValues: defaultValues ?? {},
    //   validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });
  React.useEffect(() => {
    // get current values of an input
    if (getValues !== null && typeof getValues !== "undefined") {
      getValues[1](formik.values[getValues[0]]);
    }
  }, [formik.values]);
  return (
    <div onChange={formik.handleSubmit}>
      {genInput("", parameterSchema, formik, defaultValues)}
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
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  defaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.bool,
      PropTypes.number,
      PropTypes.object,
    ])
  ),
  onFormSubmit: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  submitButton: PropTypes.bool,
  getValues: PropTypes.arrayOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.func])
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
