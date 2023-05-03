import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { FormControl, FormControlLabel, Checkbox } from "@mui/material";

function BooleanInput({ name, value, onChange, error, description }) {
  return (
    <div key={name}>
      <FormControl error={error}>
        <FormControlLabel
          label={name}
          control={<Checkbox name={name} checked={value} onChange={onChange} />}
        />
      </FormControl>
      <FormTooltip contentStr={description} />
    </div>
  );
}
BooleanInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
BooleanInput.defaultProps = {
  error: undefined,
};

export default BooleanInput;
