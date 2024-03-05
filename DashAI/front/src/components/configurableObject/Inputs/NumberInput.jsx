import React from "react";
import PropTypes from "prop-types";
import FormInputWrapper from "./FormInputWrapper";
import InputWithDebounce from "../../shared/InputWithDebounce";
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
function NumberInput({ name, value, onChange, description, error }) {
  const handleChange = (inputValue) => {
    const newValue = inputValue === "" ? null : Number(inputValue);
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
        type="number"
        error={error !== undefined}
        helperText={error || " "}
        margin="dense"
      />
    </FormInputWrapper>
  );
}
NumberInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
NumberInput.defaultProps = {
  value: null,
  error: undefined,
};

export default NumberInput;
