import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { Chip, Tooltip } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { useFormSchemaStore } from "../../contexts/schema";
import FormTooltip from "../configurableObject/FormTooltip";
import TextWithOptions from "./TextWithOptions";

/**
 * This component is a subform for the form schema
 * @param {string} name - The name of the subform
 * @param {string} label - The label of the subform
 * @param {string} description - The description of the subform
 * @param {string} errorMessage - The error message of the subform
 * @param {object} children - The children of the subform
 */

function FormSchemaFieldWithParent({ name, label, description, errorMessage }) {
  const { addProperty, getModelFromCurrentProperty } = useFormSchemaStore();

  const handleClick = () => {
    addProperty({ key: name, label });
  };

  return (
    <TextWithOptions label={label} key={name} error={Boolean(errorMessage)}>
      <Tooltip title="Configure property model">
        <Chip
          color="primary"
          size="small"
          onClick={handleClick}
          label={getModelFromCurrentProperty(name)}
          deleteIcon={<ModeEditIcon />}
          onDelete={handleClick}
        />
      </Tooltip>
      <FormTooltip
        contentStr={errorMessage ?? description}
        error={Boolean(errorMessage)}
      />
    </TextWithOptions>
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
