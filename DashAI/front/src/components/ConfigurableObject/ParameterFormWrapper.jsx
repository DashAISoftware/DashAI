import React from "react";
import ParameterForm from "./ParameterForm";
import PropTypes from "prop-types";
import { getDefaultValues } from "../../utils/values";
import uuid from "react-uuid";

function ParameterFormWrapper({ parameterSchema }) {
  const [defaultValues, setDefaultValues] = React.useState(
    getDefaultValues(parameterSchema)
  );
  React.useEffect(() => {
    const dv = getDefaultValues(parameterSchema);
    setDefaultValues(dv);
  }, [parameterSchema]);

  return (
    <ParameterForm
      parameterSchema={parameterSchema}
      defaultValues={defaultValues}
      key={uuid()}
    />
  );
}

ParameterFormWrapper.propTypes = {
  parameterSchema: PropTypes.objectOf(
    PropTypes.oneOfType([PropTypes.string, PropTypes.bool, PropTypes.object])
  ).isRequired,
};

export default ParameterFormWrapper;
