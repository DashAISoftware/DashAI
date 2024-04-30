/* eslint-disable react/prop-types */
import { Chip, Grid } from "@mui/material";
import React from "react";

const SingleSelectChipGroup = ({ options, onChange, selected }) => {
  const handleChipClick = (option) => {
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
            variant={selected === option.key ? "filled" : "outlined"}
            onClick={() => handleChipClick(option.key)}
            color={selected === option.key ? "primary" : "default"}
          />
        </Grid>
      ))}
    </Grid>
  );
};

export default SingleSelectChipGroup;
