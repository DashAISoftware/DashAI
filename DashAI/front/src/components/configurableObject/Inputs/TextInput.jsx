import PropTypes from "prop-types";
import React from "react";
import InputWithDebounce from "../../shared/InputWithDebounce";
import FormInputWrapper from "./FormInputWrapper";
/**
 * This code implements a component that renders a text form field, enabling users to enter text input.
 * @param {string} name name of the input to use as an identifier
 * @param {string} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */
function TextInput({
  name,
  label,
  value = "",
  onChange,
  error = undefined,
  description,
  ...props
}) {
  const isEmpty = value === undefined || value === "";
  const showError = error || (isEmpty ? `${name} is a required field` : "");

  return (
    <FormInputWrapper name={name} description={description}>
      <InputWithDebounce
        {...props}
        size="small"
        name={name}
        label={label}
        // A null value is an empty box, not the word "none". Displaying the
        // literal was a work-in-progress line from 2024 that only stayed
        // harmless because the null branch renders this input disabled: with
        // the input enabled it would be a submittable string.
        value={value ?? ""}
        onChange={onChange}
        autoComplete="off"
        error={!!showError}
        helperText={showError || " "}
        margin="dense"
      />
    </FormInputWrapper>
  );
}
TextInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  disabled: PropTypes.bool,
};

export default TextInput;
