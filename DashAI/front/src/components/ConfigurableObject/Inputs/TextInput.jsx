import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";

function TextInput({ name, value, onChange, error, description }) {
  return (
    <div key={name}>
      <Input
        name={name}
        label={name}
        defaultValue={value}
        onKeyUp={onChange}
        error={error}
        helperText={error}
        margin="dense"
      />
      <FormTooltip contentStr={description} />
    </div>
  );
}
TextInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
TextInput.defaultProps = {
  value: "",
  error: undefined,
};

export default TextInput;
