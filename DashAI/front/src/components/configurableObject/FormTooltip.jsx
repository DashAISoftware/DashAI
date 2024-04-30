import React from "react";
import { Tooltip, IconButton, Typography } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import PropTypes from "prop-types";
/**
 * This component renders a tooltip containing a description for each parameter in a form,
 * providing users with additional information to better understand the purpose of each input field.
 * @param {string} contentStr content of the tooltip that describes the parameter
 */
function FormTooltip({ contentStr, error }) {
  return (
    <Tooltip
      title={<Typography variant="body2">{contentStr}</Typography>}
      placement="bottom"
      arrow
    >
      <IconButton color={error ? "error" : "default"}>
        {error ? <HelpOutlineIcon color="error" /> : <HelpOutlineIcon />}
      </IconButton>
    </Tooltip>
  );
}

FormTooltip.propTypes = {
  contentStr: PropTypes.string.isRequired,
  error: PropTypes.bool,
};

export default FormTooltip;
