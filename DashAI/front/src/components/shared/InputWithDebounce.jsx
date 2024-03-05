import React, { useEffect, useState } from "react";
import { Input } from "../configurableObject/Inputs/InputStyles";
import useDebounce from "../../hooks/useDebounce";
import PropTypes from "prop-types";

export default function InputWithDebounce({
  value: defaultValue = null,
  onChange,
  ...rest
}) {
  const [value, setValue] = useState(defaultValue);

  const debounceValue = useDebounce({ value, delay: 500 });

  const handleOnChange = (e) => {
    setValue(e.target.value);
  };

  useEffect(() => {
    if (debounceValue !== undefined) {
      onChange(debounceValue);
    }
  }, [debounceValue]);

  useEffect(() => {
    if (defaultValue === "") {
      setValue(defaultValue);
    }
  }, [defaultValue]);

  return <Input {...rest} value={value} onChange={handleOnChange} />;
}

InputWithDebounce.propTypes = {
  value: PropTypes.any,
  onChange: PropTypes.func.isRequired,
};
