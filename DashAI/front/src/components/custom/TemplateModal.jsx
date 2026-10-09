import React from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
  Typography,
} from "@mui/material";

export default function TemplateModal({
  open,
  handleClose,
  template,
  title = "Prompt",
  formatText = true,
}) {
  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>{title}</DialogTitle>
      <DialogContent>
        <DialogContentText component="div">
          <Typography
            variant="body1"
            sx={{
              whiteSpace: formatText ? "pre-wrap" : "normal",
              wordBreak: "break-word",
            }}
          >
            {template}
          </Typography>
        </DialogContentText>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose} autoFocus>
          Close
        </Button>
      </DialogActions>
    </Dialog>
  );
}

TemplateModal.propTypes = {
  open: PropTypes.bool.isRequired,
  handleClose: PropTypes.func.isRequired,
  template: PropTypes.string,
  title: PropTypes.string,
  formatText: PropTypes.bool,
};
