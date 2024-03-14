import PropTypes from "prop-types";
import React from "react";
import { Input } from "../configurableObject/Inputs/InputStyles";

export default function InputWithDebounce({
  onChange,
  delay = 300,
  value,
  ...rest
}) {
  //   const [inputValue, setInputValue] = useState(value);
  //   const debouncedValue = useDebounce(inputValue, delay);

  const handleChange = (event) => {
    onChange(event.target.value);
  };

  //   useEffect(() => {
  //     onChange(debouncedValue);
  //   }, [debouncedValue, onChange]);

  return <Input value={value} onChange={handleChange} {...rest} />;
}

InputWithDebounce.propTypes = {
  value: PropTypes.any,
  delay: PropTypes.number,
  onChange: PropTypes.func.isRequired,
};
