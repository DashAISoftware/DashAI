import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { Box, Chip, IconButton, MenuItem, Tooltip } from "@mui/material";
import PropTypes from "prop-types";
import { Input } from "../configurableObject/Inputs/InputStyles";
import React from "react";
import { useFormSchemaStore } from "../../contexts/schema";
import FormTooltip from "../configurableObject/FormTooltip";
import TextWithOptions from "./TextWithOptions";
import {
  formattedModel,
  formattedSubform,
  generateYupSchema,
  getModelFromSubform,
} from "../../utils/schema";
import useModelParents from "../../hooks/useModelParents";
import { Settings } from "@mui/icons-material";

/**
 * This component is a subform for the form schema
 * @param {string} name - The name of the subform
 * @param {string} label - The label of the subform
 * @param {string} description - The description of the subform
 * @param {string} errorMessage - The error message of the subform
 * @param {object} children - The children of the subform
 */

function FormSchemaFieldWithParent({
  name,
  label,
  field,
  description,
  errorMessage,
}) {
  const { addProperty, getModelFromCurrentProperty } = useFormSchemaStore();
  const { models } = useModelParents({
    parent: field.value?.properties.component,
  });

  const handleOnChange = async (event) => {
    const model = models?.find((model) => model.name === event.target.value);
    const { initialValues } = generateYupSchema(
      await formattedModel(model?.schema),
    );

    field.onChange(
      formattedSubform({
        parent: field.value?.properties.component,
        model: model?.name,
        params: initialValues,
      }),
    );
  };

  const handleClick = () => {
    addProperty({ key: name, label });
  };

  return (
    <Box sx={{ display: "flex", alignItems: "center", pb: 3 }}>
      <Input
        select
        label={label}
        value={getModelFromCurrentProperty(name)}
        onChange={handleOnChange}
      >
        {models?.map((model, index) => (
          <MenuItem key={index} value={model.name}>
            {model.name}
          </MenuItem>
        ))}
      </Input>
      <Tooltip title="Configure submodel">
        <IconButton onClick={handleClick}>
          <Settings />
        </IconButton>
      </Tooltip>
      <FormTooltip
        contentStr={errorMessage ?? description}
        error={Boolean(errorMessage)}
      />
    </Box>
  );
}

FormSchemaFieldWithParent.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
  children: PropTypes.node,
};

export default FormSchemaFieldWithParent;
