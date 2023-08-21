import React from "react";
import PropTypes from "prop-types";
import { MenuItem } from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";
import { Input } from "./InputStyles";
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
  setFieldValue,
  error,
  description,
  options,
  optionNames,
}) {
  const handleChange = (event) => {
    const inputName = event.target.name;
    const inputValue = event.target.value;
    const newValue = inputValue === "" ? null : inputValue;
    setFieldValue(inputName, newValue);
  };

  return (
    <FormInputWrapper name={name} description={description}>
      <Input
        select
        name={name}
        label={name}
        value={value !== null ? value : ""}
        onChange={handleChange}
        error={error !== undefined}
        helperText={error || " "}
        margin="dense"
      >
        {options.map((option, index) => (
          <MenuItem key={option} value={option}>
            {optionNames !== undefined ? optionNames[index] : option}
          </MenuItem>
        ))}
      </Input>
    </FormInputWrapper>
  );
}
SelectInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  setFieldValue: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  optionNames: PropTypes.arrayOf(PropTypes.string),
};
SelectInput.defaultProps = {
  value: null,
  error: undefined,
  optionNames: undefined,
};

export default SelectInput;
