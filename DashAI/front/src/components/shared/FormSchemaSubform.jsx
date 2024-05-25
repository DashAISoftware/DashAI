import { Box, Collapse, IconButton, Typography } from "@mui/material";
import React from "react";
import ModeEditIcon from "@mui/icons-material/ModeEdit";
import { useFormSchemaStore } from "../../contexts/schema";
import FormTooltip from "../configurableObject/FormTooltip";
import PropTypes from "prop-types";

/**
 * This component is a subform for the form schema
 * @param {string} name - The name of the subform
 * @param {string} label - The label of the subform
 * @param {string} description - The description of the subform
 * @param {string} errorMessage - The error message of the subform
 * @param {object} children - The children of the subform
 */

function FormSchemaSubform({
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
      <Box
        key={name}
        display="flex"
        sx={{ width: "100%", pb: 2 }}
        alignItems="center"
        justifyContent={"space-between"}
      >
        <Box
          flex={1}
          sx={{
            whiteSpace: "nowrap",
            color: errorMessage ? "error.main" : null,
          }}
        >
          <Typography>{label}</Typography>
        </Box>
        <Box display="flex">
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
        </Box>
      </Box>
      <Collapse in={showSection}>{children}</Collapse>
    </>
  );
}

FormSchemaSubform.propTypes = {
  name: PropTypes.string.isRequired,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
  children: PropTypes.node,
};

export default FormSchemaSubform;
