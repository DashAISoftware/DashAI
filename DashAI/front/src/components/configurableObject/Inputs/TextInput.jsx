import React from "react";
import PropTypes from "prop-types";
import { Input } from "./InputStyles";
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
function TextInput({ name, value, onChange, error, description }) {
  return (
    <FormInputWrapper name={name} description={description}>
      <Input
        name={name}
        label={name}
        defaultValue={value}
        onKeyUp={onChange}
        autoComplete="off"
        error={error !== undefined}
        helperText={error || " "}
        margin="dense"
      />
    </FormInputWrapper>
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
