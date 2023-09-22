import React from "react";
import PropTypes from "prop-types";
import FormInputWrapper from "./FormInputWrapper";
import { Input } from "./InputStyles";
/**
 * This component renders a form field that accepts input for both integer and float numbers.
 * However, since there are already other components in place to handle inputs for these data types,
 * it is recommended to remove this component in the future once the necessary changes
 * have been made to the JSON objects in the backend.
 * @param {string} name name of the input to use as an identifier
 * @param {number} value the value of the input
 * @param {function} onChange function to manage changes in the input
 * @param {string} error text to indicate the reason the validation failed, undefined if there are no errors in validation
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 *
 */
function NumberInput({ name, value, setFieldValue, description, error }) {
  const handleChange = (event) => {
    const inputName = event.target.name;
    const inputValue = event.target.value;
    const newValue = inputValue === "" ? null : Number(inputValue);
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
        type="number"
        error={error !== undefined}
        helperText={error || " "}
        margin="dense"
      />
    </FormInputWrapper>
  );
}
NumberInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  setFieldValue: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
NumberInput.defaultProps = {
  value: null,
  error: undefined,
};

export default NumberInput;
