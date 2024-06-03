import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { Collapse, IconButton } from "@mui/material";
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

function FormSchemaFieldWithCollapse({
  name,
  label,
  description,
  errorMessage,
  children,
}) {
  const { addProperty } = useFormSchemaStore();
  const [showSection, setShowSection] = React.useState(false);

  const handleClick = () => {
    if (!children) {
      addProperty({ key: name, label });
    } else {
      setShowSection(!showSection);
    }
  };

  return (
    <>
      <TextWithOptions label={label}>
        <IconButton
          color={errorMessage ? "error" : "primary"}
          component="label"
          onClick={handleClick}
        >
          <ModeEditIcon />
        </IconButton>
        <FormTooltip
          contentStr={errorMessage ?? description}
          error={Boolean(errorMessage)}
        />
      </TextWithOptions>
      <Collapse in={showSection}>{children}</Collapse>
    </>
  );
}

FormSchemaFieldWithCollapse.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
  children: PropTypes.node,
};

export default FormSchemaFieldWithCollapse;
