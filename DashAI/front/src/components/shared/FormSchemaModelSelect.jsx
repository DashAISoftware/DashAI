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
import PropTypes from "prop-types";

/**
 * This component is a select input for the models of a parent model
 * @param {string} parent - The parent model
 * @param {string} selectedModel - The selected model
 * @param {function} onChange - The function to update the selected model
 */

function FormSchemaModelSelect({ parent, selectedModel, onChange }) {
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

FormSchemaModelSelect.propTypes = {
  parent: PropTypes.string.isRequired,
  selectedModel: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default FormSchemaModelSelect;
