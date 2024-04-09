/* eslint-disable react/prop-types */
import { FormControl, MenuItem } from "@mui/material";
import React from "react";
import useModelParents from "../../hooks/useModelParents";
import { Input } from "../configurableObject/Inputs/InputStyles";
import { useFormSchemaStore } from "../../contexts/schema";
import {
  formattedModel,
  formattedSubform,
  generateYupSchema,
} from "../../utils/schema";

function FormSchemaSelect({ parent, selectedModel, onChange }) {
  const { models } = useModelParents({ parent });
  const { handleUpdateSchema } = useFormSchemaStore();

  if (!models || !selectedModel) {
    return null;
  }

  const handleOnChange = async (event) => {
    const model = models.find((model) => model.name === event.target.value);
    const { initialValues } = generateYupSchema(
      await formattedModel(model.schema),
    );
    handleUpdateSchema(
      formattedSubform({ parent, model: model.name, params: initialValues }),
    );
    onChange(event.target.value);
  };

  return (
    <FormControl sx={{ width: "auto" }}>
      <Input
        select
        label="Select a model"
        value={selectedModel}
        onChange={handleOnChange}
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

export default FormSchemaSelect;
