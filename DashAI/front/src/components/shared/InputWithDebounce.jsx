/* eslint-disable no-unused-vars */
import PropTypes from "prop-types";
import React, { useEffect, useState } from "react";
import { Input } from "../configurableObject/Inputs/InputStyles";
import useDebounce from "../../hooks/useDebounce";

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
