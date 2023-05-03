import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";

function NumberInput({ name, value, onChange, description, error }) {
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
        margin="dense"
      />
      <FormTooltip contentStr={description} />
    </div>
  );
}
NumberInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
NumberInput.defaultProps = {
  error: undefined,
};

export default NumberInput;
