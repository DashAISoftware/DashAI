import React from "react";
import PropTypes from "prop-types";
import {
  FormControl,
  FormControlLabel,
  Checkbox,
  FormHelperText,
} from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";
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
    <FormInputWrapper name={name} description={description}>
      <FormControl error={error !== undefined}>
        <FormControlLabel
          label={name}
          control={<Checkbox name={name} checked={value} onChange={onChange} />}
        />
        <FormHelperText>{error || " "}</FormHelperText>
      </FormControl>
    </FormInputWrapper>
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
