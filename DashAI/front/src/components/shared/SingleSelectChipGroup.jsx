import { Chip, Grid } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

/**
 * This component is a single select chip group
 * @param {Array} options - The options to display
 * @param {function} onChange - The function to update the selected option
 * @param {string} selected - The selected option
 */

const SingleSelectChipGroup = ({ options, onChange, selected }) => {
  const handleChipClick = (option) => {
    onChange(option);
  };

  return (
    <Grid container spacing={1}>
      {options.map((option, index) => (
        <Grid item key={"option-" + option.key + "-" + index}>
          <Chip
            label={option.label}
            sx={{ borderRadius: 2 }}
            clickable
            variant={selected === option.key ? "filled" : "outlined"}
            onClick={() => handleChipClick(option.key)}
            color={selected === option.key ? "primary" : "default"}
          />
        </Grid>
      ))}
    </Grid>
  );
};

SingleSelectChipGroup.propTypes = {
  options: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  selected: PropTypes.string.isRequired,
};

export default SingleSelectChipGroup;
