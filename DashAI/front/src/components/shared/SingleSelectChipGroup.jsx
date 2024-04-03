/* eslint-disable react/prop-types */
import React, { useState } from "react";
import { Chip, Grid } from "@mui/material";

const SingleSelectChipGroup = ({ options, onChange, selected }) => {
  const [selectedOption, setSelectedOption] = useState(selected);

  const handleChipClick = (option) => {
    setSelectedOption(option);
    onChange(option);
  };

  return (
    <Grid container spacing={1}>
      {options.map((option) => (
        <Grid item key={option.key}>
          <Chip
            label={option.label}
            sx={{ borderRadius: 2 }}
            clickable
            variant={selectedOption === option.key ? "filled" : "outlined"}
            onClick={() => handleChipClick(option.key)}
            color={selectedOption === option.key ? "primary" : "default"}
          />
        </Grid>
      ))}
    </Grid>
  );
};

export default SingleSelectChipGroup;
