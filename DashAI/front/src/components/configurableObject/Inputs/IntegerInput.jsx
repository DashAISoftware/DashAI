import React from "react";
import PropTypes from "prop-types";
import FormInputWrapper from "./FormInputWrapper";
import InputWithDebounce from "../../shared/InputWithDebounce";
/**
 * renders a form field that accepts input for integer numbers.
 * @param {string} name name of the input to use as an identifier
 * @param {number} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */
function IntegerInput({ name, value, onChange, description, error }) {
  const handleChange = (inputValue) => {
    const newValue = inputValue === "" ? null : parseInt(inputValue);
    onChange(newValue);
  };

  return (
    <FormInputWrapper name={name} description={description}>
      <InputWithDebounce
        variant="outlined"
        label={name}
        name={name}
        value={value !== null ? value : ""}
        onChange={handleChange}
        error={error !== undefined}
        helperText={error || " "}
        type="number"
        margin="dense"
      />
    </FormInputWrapper>
  );
}
IntegerInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.PropTypes.number,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
IntegerInput.defaultProps = {
  value: null,
  error: undefined,
};

export default IntegerInput;
