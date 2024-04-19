import React, { useState } from "react";
import {
  Grid,
  Typography,
  IconButton,
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogContentText,
  DialogActions,
  Button,
} from "@mui/material";
import DeleteIcon from "@mui/icons-material/Delete";
import ZoomInIcon from "@mui/icons-material/ZoomIn";
import PropTypes from "prop-types";
import ExplainersPlot from "./ExplainersPlot";
import { deleteExplainer } from "../../api/explainer";

/**
 * GlobalExplainersCard
 * @param {*} explainer
 * @returns Component that render a card for the explainer
 */
export default function ExplainersCard({ explainer, scope }) {
  const [open, setOpen] = useState(false);

  function plotName(name) {
    return name.match(/[A-Z][a-z]+|[0-9]+/g).join(" ");
  }

  const handleDeleteExplainer = () => {
    setOpen(true);
  };

  const handleClose = () => {
    setOpen(false);
  };

  return (
    <Paper elevation={3}>
      <Grid container item minWidth={800} maxWidth={800} p={4} gap={2}>
        <Grid
          item
          container
          direction={"row"}
          justifyContent={"space-between"}
          alignItems={"center"}
        >
          <Grid item>
            <Typography variant="h6">
              {plotName(explainer.explainer_name)} Plot
            </Typography>
            <Typography variant="h7">
              Explainer name: {explainer.name}
            </Typography>
          </Grid>
          <Grid item>
            <IconButton aria-label="zoomin">
              <ZoomInIcon />
            </IconButton>
            <IconButton
              aria-label="delete"
              color="error"
              onClick={handleDeleteExplainer}
            >
              <DeleteIcon />
            </IconButton>
            <Dialog
              open={open}
              onClose={handleClose}
              aria-labelledby="alert-dialog-title"
              aria-describedby="alert-dialog-description"
            >
              <DialogTitle id="alert-dialog-title">
                {"Delete explainer?"}
              </DialogTitle>
              <DialogContent>
                <DialogContentText id="alert-dialog-description">
                  If you delete the explainer it will be removed with it is
                  corresponding plot, in case it has one.
                </DialogContentText>
              </DialogContent>
              <DialogActions>
                <Button onClick={handleClose}>Disagree</Button>
                <Button
                  onClick={() => {
                    deleteExplainer(scope, explainer.id);
                    handleClose();
                  }}
                  autoFocus
                >
                  Agree
                </Button>
              </DialogActions>
            </Dialog>
          </Grid>
        </Grid>
        <ExplainersPlot explainer={explainer} scope={scope} />
      </Grid>
    </Paper>
  );
}

// Duda: por qué algunas están en camelCase?
ExplainersCard.propTypes = {
  explainer: PropTypes.shape({
    explainer_name: PropTypes.string,
    id: PropTypes.number,
    parameters: PropTypes.objectOf(
      PropTypes.oneOfType([
        PropTypes.number,
        PropTypes.string,
        PropTypes.arrayOf(PropTypes.string),
      ]),
    ),
    status: PropTypes.number,
    runId: PropTypes.number,
    explanationPath: PropTypes.string,
    plot_path: PropTypes.string,
    name: PropTypes.string,
    created: PropTypes.string,
  }).isRequired,
  scope: PropTypes.string.isRequired,
};
