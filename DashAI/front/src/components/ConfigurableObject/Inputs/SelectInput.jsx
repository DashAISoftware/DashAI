import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "./InputStyles";
import { MenuItem } from "@mui/material";
/**
 * This component renders a dropdown form field, allowing users to select from a list of options.
 * @param {string} name name of the input to use as an identifier
 * @param {string} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 * @param {Array.<string>} options the list of options for the dropdown
 *
 */
function SelectInput({
  name,
  value,
  onChange,
  error,
  description,
  options,
  optionNames,
}) {
  return (
    <div key={name}>
      <Input
        select
        name={name}
        label={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      >
        {options.map((option, index) => (
          <MenuItem key={option} value={option}>
            {optionNames !== undefined ? optionNames[index] : option}
          </MenuItem>
        ))}
      </Input>
      <FormTooltip contentStr={description} />
    </div>
  );
}
SelectInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  optionNames: PropTypes.arrayOf(PropTypes.string),
};
SelectInput.defaultProps = {
  error: undefined,
  optionNames: undefined,
};

export default SelectInput;
