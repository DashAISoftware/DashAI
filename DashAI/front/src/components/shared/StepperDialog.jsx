import { Dialog } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

function StepperDialog({ open, onClose, children }) {
  return (
    <Dialog
      open={open}
      fullWidth
      maxWidth={"lg"}
      onClose={onClose}
      aria-labelledby="new-experiment-dialog-title"
      aria-describedby="new-experiment-dialog-description"
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {children}
    </Dialog>
  );
}

StepperDialog.propTypes = {
  onClose: PropTypes.func.isRequired,
  open: PropTypes.bool.isRequired,
  children: PropTypes.node.isRequired,
};

export default StepperDialog;
