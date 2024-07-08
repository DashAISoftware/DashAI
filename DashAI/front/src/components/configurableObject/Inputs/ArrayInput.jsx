import React from "react";
import PropTypes from "prop-types";
import InputWithDebounce from "../../shared/InputWithDebounce";
import { FormControl, FormHelperText } from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";

function ArrayInput({ name, label, value, onChange, error, description, ...props }) {
  const handleChange = (newValue) => {
    // Convert the comma-separated string to an array of integers
    const arrayValue = newValue.split(',').map((item) => parseInt(item, 10)).filter((item) => !isNaN(item));
    onChange(arrayValue);
  };

  return (
    <FormInputWrapper name={name} description={description}>
      <FormControl error={!!error}>
        <InputWithDebounce
          {...props}
          name={name}
          label={label}
          value={value.join(',')}
          onChange={handleChange}
          autoComplete="off"
          error={!!error}
          helperText={error || " "}
          margin="dense"
        />
        <FormHelperText>{error || " "}</FormHelperText>
      </FormControl>
    </FormInputWrapper>
  );
}

ArrayInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.arrayOf(PropTypes.number),
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};

ArrayInput.defaultProps = {
  value: [],
  error: undefined,
};

export default ArrayInput;
