import React from "react";
import PropTypes from "prop-types";
import FormInputWrapper from "./FormInputWrapper";
import { Input } from "./InputStyles";
/**
 * renders a form field that accepts input for integer numbers.
 * @param {string} name name of the input to use as an identifier
 * @param {number} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */
function IntegerInput({ name, value, setFieldValue, description, error }) {
  const handleChange = (event) => {
    const inputName = event.target.name;
    const inputValue = event.target.value;
    const newValue = inputValue === "" ? null : parseInt(inputValue);
    setFieldValue(inputName, newValue);
  };

  return (
    <FormInputWrapper name={name} description={description}>
      <Input
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
  setFieldValue: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
IntegerInput.defaultProps = {
  value: null,
  error: undefined,
};

export default IntegerInput;
