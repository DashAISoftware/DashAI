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

function TextWithOptions({ label, error, children }) {
  return (
    <Box
      display="flex"
      sx={{ width: "100%", pb: 2 }}
      alignItems="center"
      justifyContent={"space-between"}
    >
      <Box
        flex={1}
        sx={{
          whiteSpace: "nowrap",
          color: error ? "error.main" : null,
        }}
      >
        <Typography>{label}</Typography>
      </Box>
      <Box display="flex" alignItems="center">
        {children}
      </Box>
    </Box>
  );
}

export default TextWithOptions;
