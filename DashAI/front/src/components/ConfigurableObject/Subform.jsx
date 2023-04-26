import React, { useEffect } from "react";
import PropTypes from "prop-types";
import { genInput } from "./FormInputs";
import { useFormik } from "formik";

function Subform({
  name,
  parameterSchema,
  setFieldValue,
  choice,
  defaultValues,
}) {
  const newDefaultValues = { ...defaultValues, choice };
  const formik = useFormik({
    initialValues: newDefaultValues,
    //   validationSchema: getValidation(parameterSchema),
  });
  useEffect(() => {
    setFieldValue(name, formik.values);
  }, [formik.values]);

  return (
    <div key={`parameterForm-${choice}`}>
      {genInput(name, parameterSchema, formik, defaultValues)}
    </div>
  );
}
Subform.propTypes = {
  name: PropTypes.string,
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  setFieldValue: PropTypes.func.isRequired,
  choice: PropTypes.string.isRequired,
  defaultValues: PropTypes.objectOf(
    PropTypes.oneOfType([
      PropTypes.string,
      PropTypes.number,
      PropTypes.bool,
      PropTypes.object,
    ])
  ),
};
Subform.defaultProps = {
  name: "undefined",
  defaultValues: { emptyDefaultValues: true },
};

export default Subform;
