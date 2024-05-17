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
function OptimizeNumberInput({ name, label, value, onChange, description, error, placeholder}) {

  const [switchState, setSwitchState] = useState(placeholder.optimize);
  const handleChangeFixed = (inputValue) => {
    const newValue = inputValue === "" ? null : Number(inputValue);
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
  if (placeholder.optimize!== undefined){
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
OptimizeNumberInput.propTypes = {
  name: PropTypes.string,
  value: PropTypes.object.isRequired,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};
OptimizeNumberInput.defaultProps = {
  value: {"fixed_value": 1.0, "lower_bound": 1.0, "optimize": false, "upper_bound": 10.0 },
  error: undefined,
};

export default OptimizeNumberInput;
