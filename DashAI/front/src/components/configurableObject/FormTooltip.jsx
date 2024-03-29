import React from "react";
import { Tooltip, IconButton } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import PropTypes from "prop-types";
/**
 * This component renders a tooltip containing a description for each parameter in a form,
 * providing users with additional information to better understand the purpose of each input field.
 * @param {string} contentStr content of the tooltip that describes the parameter
 */
function FormTooltip({ contentStr }) {
  return (
    <Tooltip
      title={<div dangerouslySetInnerHTML={{ __html: contentStr }} />}
      placement="right-start"
      arrow
    >
      <IconButton>
        <HelpOutlineIcon />
      </IconButton>
    </Tooltip>
  );
}

FormTooltip.propTypes = {
  contentStr: PropTypes.string.isRequired,
};

export default FormTooltip;
