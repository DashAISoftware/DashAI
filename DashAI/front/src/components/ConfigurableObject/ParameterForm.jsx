import React from "react";
import MainForm from "./MainForm";
import PropTypes from "prop-types";
import { getDefaultValues } from "../../utils/values";
import uuid from "react-uuid";

function ParameterForm({
  parameterSchema,
  extraOptions,
  submitButton,
  onFormSubmit,
}) {
  const [defaultValues, setDefaultValues] = React.useState(
    getDefaultValues(parameterSchema)
  );
  React.useEffect(() => {
    const dv = getDefaultValues(parameterSchema);
    setDefaultValues(dv);
  }, [parameterSchema]);

  return (
    <MainForm
      parameterSchema={parameterSchema}
      defaultValues={defaultValues}
      onFormSubmit={onFormSubmit}
      extraOptions={extraOptions}
      submitButton={submitButton}
      key={uuid()}
    />
  );
}

ParameterForm.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
  onFormSubmit: PropTypes.func,
  extraOptions: PropTypes.shape({}),
  submitButton: PropTypes.bool,
};
ParameterForm.defaultProps = {
  onFormSubmit: () => {},
  extraOptions: null,
  submitButton: false,
};
export default ParameterForm;
