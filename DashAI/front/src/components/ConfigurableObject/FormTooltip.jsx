import React from "react";
import { Tooltip, IconButton } from "@mui/material";
import HelpOutlineIcon from "@mui/icons-material/HelpOutline";
import PropTypes from "prop-types";

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
