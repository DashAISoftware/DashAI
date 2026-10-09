import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import InputWithDebounce from "../../shared/InputWithDebounce";
import { FormControl } from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";

function ArrayInput({
  name,
  label,
  value = [],
  onChange,
  error = undefined,
  description,
  itemType,
  ...props
}) {
  // Ensure value is an array before using join
  const safeValue = Array.isArray(value) ? value : [];
  const [inputValue, setInputValue] = useState(safeValue.join(","));

  // Update inputValue when value prop changes
  useEffect(() => {
    const newSafeValue = Array.isArray(value) ? value : [];
    setInputValue(newSafeValue.join(","));
  }, [value]);

  useEffect(() => {
    if (Array.isArray(value)) {
      setInputValue(value.join(","));
    }
  }, [value]);

  const convertValue = (val) => {
    switch (itemType) {
      case "integer":
        return parseInt(val);
      case "number":
        return parseFloat(val);
      default:
        return val;
    }
  };
  const handleChange = (newValue) => {
    const arrayValue = newValue.split(",");
    setInputValue(arrayValue);
    const removeEmpty = arrayValue
      .filter((item) => item !== "")
      .map((item) => convertValue(item));
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
          helperText={error}
        />
      </FormControl>
    </FormInputWrapper>
  );
}

ArrayInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.arrayOf(PropTypes.any),
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  itemType: PropTypes.string,
};

export default ArrayInput;
