import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { Input } from "../configurableObject/Inputs/InputStyles";
import useDebounce from "../../hooks/useDebounce";
import { width } from "@mui/system";

/**
 * This is a HOC for an input with a debounce, it will update the value after a delay,
 * useful when you want to wait for the user to stop typing before updating the value
 * @param {function} onChange - The function to update the value
 * @param {number} delay - The delay to wait before updating the value
 * @param {any} value - The value to update
 * @param {function} onBlur - Optional blur handler forwarded to the input
 */

export default function InputWithDebounce({
  onChange,
  delay = 300,
  value,
  onBlur,
  ...rest
}) {
  const [inputValue, setInputValue] = useState(value);
  const debouncedValue = useDebounce(inputValue, delay);

  const handleChange = (event) => {
    setInputValue(event.target.value);
  };

  // Commit a pending edit before the field loses focus. Without this, an
  // action that reads the parent state immediately after the click (such as
  // the dialog's Done button) can run before the debounce fires and persist
  // the previous value.
  const handleBlur = (event) => {
    // Normalize both sides to the wire form the change handler expects. Array
    // inputs keep their value as a list locally but consume comma-separated
    // text, and numeric inputs receive a string from the DOM event.
    const inputText = Array.isArray(inputValue)
      ? inputValue.join(",")
      : String(inputValue);
    const currentText = Array.isArray(value) ? value.join(",") : String(value);
    if (inputText !== currentText) {
      onChange(inputText);
    }
    if (onBlur) {
      onBlur(event);
    }
  };

  useEffect(() => {
    if (debouncedValue !== value) {
      onChange(debouncedValue);
    }
  }, [debouncedValue]);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  return (
    <Input
      value={inputValue}
      onChange={handleChange}
      onBlur={handleBlur}
      {...rest}
    />
  );
}

InputWithDebounce.propTypes = {
  value: PropTypes.any,
  delay: PropTypes.number,
  onChange: PropTypes.func.isRequired,
  onBlur: PropTypes.func,
};
