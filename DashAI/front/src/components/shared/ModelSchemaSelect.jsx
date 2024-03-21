/* eslint-disable react/prop-types */
import { FormControl, MenuItem } from "@mui/material";
import React from "react";
import useModelParents from "../../hooks/useModelParents";
import { Input } from "../configurableObject/Inputs/InputStyles";

function ModelSchemaSelect({ parent, selectedModel, onChange }) {
  console.log(parent);
  const { models } = useModelParents({ parent });

  if (!models || !selectedModel) {
    return null;
  }

  const handleOnChange = (event) => {
    onChange(event.target.value);
  };
  return (
    <FormControl fullWidth>
      <Input
        select
        label="Select a model"
        value={selectedModel}
        onChange={handleOnChange}
        fullWidth
      >
        {models?.map((model, index) => (
          <MenuItem key={index} value={model.name}>
            {model.name}
          </MenuItem>
        ))}
      </Input>
    </FormControl>
  );
}

export default ModelSchemaSelect;
