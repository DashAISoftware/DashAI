import React from "react";
import PropTypes from "prop-types";
import { ListItemText, MenuItem } from "@mui/material";
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
  value = null,
  label,
  onChange,
  error = undefined,
  description,
  options,
  optionNames = undefined,
  disabled = false,
}) {
  const handleChange = (event) => {
    const inputValue = event.target.value;
    // "" means "nothing selected" only when it is not itself an option. Plotly's
    // histnorm offers it as a real value meaning raw counts, and coercing it to
    // null made that option unselectable: the backend rejected the null for a
    // field that does not admit one, so the default could never be restored.
    const emptyIsAnOption = Array.isArray(options) && options.includes("");
    const newValue = inputValue === "" && !emptyIsAnOption ? null : inputValue;
    onChange(newValue);
  };

  // Include current value in options if it's not already there
  const allOptions =
    value !== null && !options.includes(value) ? [...options, value] : options;

  return (
    <FormInputWrapper name={name} description={description}>
      <Input
        select
        size="small"
        disabled={disabled}
        name={name}
        label={label}
        value={value !== null ? value : ""}
        onChange={handleChange}
        error={error !== undefined}
        helperText={error}
      >
        {allOptions.map((option, index) => (
          <MenuItem key={option} value={option}>
            <ListItemText
              slotProps={{
                primary: {
                  sx: {
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    whiteSpace: "nowrap",
                    maxWidth: "100%",
                    display: "block",
                  },
                },
              }}
              primary={
                optionNames !== undefined && index < options.length
                  ? optionNames[index]
                  : option
              }
            />
          </MenuItem>
        ))}
      </Input>
    </FormInputWrapper>
  );
}
SelectInput.propTypes = {
  disabled: PropTypes.bool,
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
  optionNames: PropTypes.arrayOf(PropTypes.string),
};

export default SelectInput;
