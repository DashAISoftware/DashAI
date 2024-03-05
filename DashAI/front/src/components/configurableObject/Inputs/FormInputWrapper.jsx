import { Box } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import FormTooltip from "../FormTooltip";
/**
 * Generic component that wraps each form input
 * @param {string} name name of the input to use as an identifier
 * @param {string} description text to put in a tooltip that helps the user to understand the parameter
 * @param {boolean} disabledPadding if true, the padding for the tooltip is disabled
 * @param {React.ReactNode} children the input component to render in the layout
 *
 */
function FormInputWrapper({
  name,
  description,
  disabledPadding = false,
  children,
}) {
  return (
    <Box display="flex" alignItems="flex-start" gap={2}>
      <Box sx={{ flex: 1 }}>{children}</Box>
      <Box sx={{ pt: disabledPadding ? 0 : 2 }}>
        <FormTooltip contentStr={description} />
      </Box>
    </Box>
  );
}
FormInputWrapper.propTypes = {
  name: PropTypes.string.isRequired,
  description: PropTypes.string.isRequired,
  disabledPadding: PropTypes.boolean,
  children: PropTypes.node.isRequired,
};

export default FormInputWrapper;
