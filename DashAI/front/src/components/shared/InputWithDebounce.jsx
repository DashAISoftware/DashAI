import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { Input } from "../configurableObject/Inputs/InputStyles";
import useDebounce from "../../hooks/useDebounce";

/**
 * This is a HOC for an input with a debounce, it will update the value after a delay,
 * useful when you want to wait for the user to stop typing before updating the value
 * @param {function} onChange - The function to update the value
 * @param {number} delay - The delay to wait before updating the value
 * @param {any} value - The value to update
 */

export default function InputWithDebounce({
  onChange,
  delay = 300,
  value,
  ...rest
}) {
  const [inputValue, setInputValue] = useState(value);
  const debouncedValue = useDebounce(inputValue, delay);

  const handleChange = (event) => {
    setInputValue(event.target.value);
  };

  useEffect(() => {
    if (debouncedValue !== value) {
      onChange(debouncedValue);
    }
  }, [debouncedValue]);

  useEffect(() => {
    setInputValue(value);
  }, [value]);

  return <Input value={inputValue} onChange={handleChange} {...rest} />;
}

InputWithDebounce.propTypes = {
  value: PropTypes.any,
  delay: PropTypes.number,
  onChange: PropTypes.func.isRequired,
};
