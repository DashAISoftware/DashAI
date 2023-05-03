import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";

function FloatInput({ name, value, onChange, description, error }) {
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        type="number"
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      />
      <FormTooltip contentStr={description} />
    </div>
  );
}
FloatInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
FloatInput.defaultProps = {
  error: undefined,
};

export default FloatInput;
