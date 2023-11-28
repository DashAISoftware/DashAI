import React, { useState } from "react";
import { Select } from "@mui/material";
import PropTypes, { string } from "prop-types";
const SelectTypeCell = ({ id, value, field, options, updateValue }) => {
  const [selectedValue, setSelectedValue] = useState(value || "");

  const handleChange = async (event) => {
    const newValue = event.target.value;
    setSelectedValue(newValue);
    updateValue(id, field, newValue);
  };

  return (
    <Select
      native
      value={selectedValue}
      onChange={handleChange}
      size="small"
      sx={{ height: 1 }}
      autoFocus
    >
      {options.map((option) => (
        <option key={option} value={option}>
          {option}
        </option>
      ))}
    </Select>
  );
};
SelectTypeCell.propTypes = {
  id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]).isRequired,
  value: PropTypes.string.isRequired,
  field: PropTypes.string.isRequired,
  options: PropTypes.arrayOf(string).isRequired,
  updateValue: PropTypes.func.isRequired,
};
export default SelectTypeCell;
