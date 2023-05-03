import React from "react";
import PropTypes from "prop-types";
import FormTooltip from "../FormTooltip";
import { Input } from "../../../styles/components/InputStyles";
import { MenuItem } from "@mui/material";

function SelectInput({ name, value, onChange, error, description, options }) {
  return (
    <div key={name}>
      <Input
        select
        name={name}
        label={name}
        value={value}
        onChange={onChange}
        error={error}
        helperText={error}
        margin="dense"
      >
        {options.map((option) => (
          <MenuItem key={option} value={option}>
            {option}
          </MenuItem>
        ))}
      </Input>
      <FormTooltip contentStr={description} />
    </div>
  );
}
SelectInput.propTypes = {
  name: PropTypes.string.isRequired,
  value: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
  options: PropTypes.arrayOf(PropTypes.string).isRequired,
};
SelectInput.defaultProps = {
  error: undefined,
};

export default SelectInput;
