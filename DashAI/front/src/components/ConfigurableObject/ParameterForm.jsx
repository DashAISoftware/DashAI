import React from "react";
import PropTypes from "prop-types";
import { Stack } from "@mui/material";
import { useFormik } from "formik";
import { genInput } from "./FormInputs";

function ParameterForm({ parameterSchema, defaultValues, onFormSubmit }) {
  const formik = useFormik({
    initialValues: defaultValues ?? {},
    //   validationSchema: getValidation(parameterSchema),
    onSubmit: (values) => {
      onFormSubmit(values);
    },
  });
  return (
    <Stack direction="column" onChange={formik.handleSubmit}>
      {genInput("", parameterSchema, formik, defaultValues)}
    </Stack>
  );
}

ParameterForm.propTypes = {
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
};

ParameterForm.defaultProps = {
  defaultValues: { emptyDefaultValues: true },
  onFormSubmit: () => {},
};

export default ParameterForm;
