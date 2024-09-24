import React, { useCallback } from "react";
import PropTypes from "prop-types";

import {
  Dialog,
  DialogTitle,
  DialogContent,
  Grid,
  Typography,
  IconButton,
  Box,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";

import { useExplorerContext } from "./context";
import { Explorer } from "./";

function ExplorerModal({ open, onClose = () => {} }) {
  const { explorerData } = useExplorerContext();
  const { datasetId, explorerId } = explorerData;

  const handleCloseContent = useCallback(
    (_e, reason) => {
      if (reason === "backdropClick") return;
      onClose();
    },
    [onClose],
  );

  return (
    <Dialog
      open={open}
      onClose={handleCloseContent}
      fullWidth
      disableEscapeKeyDown
      maxWidth="lg"
    >
      <DialogTitle>
        <Grid container justifyContent="space-between" alignItems="center">
          <Grid item>
            Explorer Module{" "}
            <Typography variant="caption" color="textSecondary">
              (Dataset ID: {datasetId}
              {explorerId && ` | Explorer ID: ${explorerId}`})
            </Typography>
          </Grid>

          <Grid item>
            <IconButton onClick={onClose} color="error">
              <CloseIcon />
            </IconButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent>
        <Box>
          <Explorer />
        </Box>
      </DialogContent>
    </Dialog>
  );
}

ExplorerModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func,
};

export default ExplorerModal;
