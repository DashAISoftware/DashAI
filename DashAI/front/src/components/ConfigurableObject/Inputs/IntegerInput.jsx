import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";
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
  return (
    <div key={name}>
      <Input
        variant="outlined"
        label={name}
        name={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        type="number"
        margin="dense"
      />
      <FormTooltip contentStr={description} />
    </div>
  );
}
IntegerInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.number.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
IntegerInput.defaultProps = {
  error: undefined,
};

export default IntegerInput;
