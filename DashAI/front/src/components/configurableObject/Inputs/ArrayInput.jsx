import React, { useState } from "react";
import PropTypes from "prop-types";
import InputWithDebounce from "../../shared/InputWithDebounce";
import { FormControl } from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";

function ArrayInput({
  name,
  label,
  value,
  onChange,
  error,
  description,
  ...props
}) {
  const [inputValue, setInputValue] = useState(value.join(","));
  const handleChange = (newValue) => {
    // Convert the comma-separated string to an array of integers
    const arrayValue = newValue.split(",").filter((item) => !isNaN(item));
    setInputValue(arrayValue);
    const removeEmpty = arrayValue.filter((item) => item !== "");
    onChange(removeEmpty);
  };

  return (
    <FormInputWrapper name={name} description={description}>
      <FormControl error={!!error}>
        <InputWithDebounce
          {...props}
          name={name}
          label={label}
          value={inputValue}
          onChange={handleChange}
          autoComplete="off"
          error={!!error}
          helperText={error || " "}
          margin="dense"
        />
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
