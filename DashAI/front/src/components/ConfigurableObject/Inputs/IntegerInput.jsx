import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";

function IntegerInput({ name, value, onChange, description, error }) {
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        type="number"
        margin="dense"
      />
      <FormTooltip contentStr={description} />
    </div>
  );
}
IntegerInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
IntegerInput.defaultProps = {
  error: undefined,
};

export default IntegerInput;
