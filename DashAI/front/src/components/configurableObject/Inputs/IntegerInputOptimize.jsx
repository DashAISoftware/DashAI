import React, { useState } from "react";
import PropTypes from "prop-types";
import FormInputWrapper from "./FormInputWrapper";
import {
  FormControl,
  FormControlLabel,
  Switch,
  FormHelperText,
} from "@mui/material";
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
function OptimizeIntegerInput({ name, label, value, onChange, description, error, placeholder }) {

  const [switchState, setSwitchState] = useState(placeholder.optimize);
  const handleChangeFixed = (inputValue) => {
    const newValue = inputValue === "" ? null : parseInt(inputValue);
    onChange({...value, fixed_value: newValue});
  };

  const handleChangeLower = (inputValue) => {
    const newValue = inputValue === "" ? null : parseInt(inputValue);
    onChange({...value, lower_bound: newValue});
  };

  const handleChangeUpper = (inputValue) => {
    const newValue = inputValue === "" ? null : parseInt(inputValue);
    onChange({...value, upper_bound: newValue});
  };

  const handleSwitchChange = () => {
    setSwitchState(!switchState) ;
    onChange({...value, optimize:!switchState});
  };
  if (placeholder.optimize !== undefined){
    return (
      <FormInputWrapper name={name} description={description}>
        <FormControl error={error !== undefined}>
         <FormControlLabel
            label={'Optimize hyperparameter "' + name+'"'}
            control={<Switch name={name} checked={switchState} onChange={handleSwitchChange} />}
            />
          <FormHelperText>{error || " "}</FormHelperText>
        </FormControl>

        {switchState ? (<>
          <InputWithDebounce
            variant="outlined"
            label={"enter a value for the lower bound of search space"}
            name={name}
            value={placeholder.lower_bound !== null ? placeholder.lower_bound : ""}
            onChange={handleChangeLower}
            error={error !== undefined}
            helperText={error || " "}
            type="number"
            margin="dense"
          />
          <InputWithDebounce
            variant="outlined"
            label={"enter a value for the upper bound of search space"}
            name={name}
            value={placeholder.upper_bound !== null ? placeholder.upper_bound : ""}
            onChange={handleChangeUpper}
            error={error !== undefined}
            helperText={error || " "}
            type="number"
            margin="dense"
          />
        </>
        ) : (
          <InputWithDebounce
            variant="outlined"
            label={"enter a value"}
            name={name}
            value={placeholder.fixed_value !== null ? placeholder.fixed_value : ""}
            onChange={handleChangeFixed}
            error={error !== undefined}
            helperText={error || " "}
            type="number"
            margin="dense"
          />
      )}

      </FormInputWrapper>
    );

  } else {
  return (
    <FormInputWrapper name={name} description={description}>
      <InputWithDebounce
        variant="outlined"
        label={"enter a value"}
        name={name}
        value={placeholder.fixed_value !== null ? placeholder.fixed_value : ""}
        onChange={handleChangeFixed}
        error={error !== undefined}
        helperText={error || " "}
        type="number"
        margin="dense"
      />
    </FormInputWrapper>
  );
  }
}

OptimizeIntegerInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.PropTypes.number,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
OptimizeIntegerInput.defaultProps = {
  value: null,
  error: undefined,
};

export default OptimizeIntegerInput;
