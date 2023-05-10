import React from "react";
import MainForm from "./MainForm";
import PropTypes from "prop-types";
import { getFullDefaultValues } from "../../utils/values";

function ParameterForm({
  parameterSchema,
  extraOptions,
  submitButton,
  onFormSubmit,
  getValues,
}) {
  const [defaultValues, setDefaultValues] = React.useState(null);
  const [loading, setLoading] = React.useState(true);
  // checks if the default values correspond to the parameterSchema
  // TODO: find a better way because this fails if the new parameterSchema has a parameter with the same name as the previous parameterSchema.
  const checkDefaultValues = () => {
    if (defaultValues === null) {
      return false;
    }
    return Object.keys(parameterSchema.properties)[0] in defaultValues;
  };
  async function getFormInitialValues() {
    setLoading(true);
    const values = await getFullDefaultValues(parameterSchema);
    setDefaultValues(values);
    setLoading(false);
  }
  React.useEffect(() => {
    getFormInitialValues();
  }, [parameterSchema]);
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
