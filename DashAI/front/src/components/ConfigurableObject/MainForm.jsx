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
}) {
  const formik = useFormik({
    initialValues: defaultValues ?? {},
    //   validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });
  return (
    <div>
      {genInput("", parameterSchema, formik, defaultValues)}
      {extraOptions}
      {submitButton && <Button onClick={formik.handleSubmit}>Save</Button>}
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
};

MainForm.defaultProps = {
  defaultValues: { emptyDefaultValues: true },
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
};

export default MainForm;
