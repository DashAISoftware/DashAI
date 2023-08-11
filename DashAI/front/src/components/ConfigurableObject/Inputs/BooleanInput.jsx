import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { FormControl, FormControlLabel, Checkbox } from "@mui/material";
/**
 * renders a checkbox to handle boolean inputs.
 * @param {string} name name of the input to use as an identifier
 * @param {bool} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */
function BooleanInput({ name, value, onChange, error, description }) {
  return (
    <div key={name}>
      <FormControl error={error !== undefined}>
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
