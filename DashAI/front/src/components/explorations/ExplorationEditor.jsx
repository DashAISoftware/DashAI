import React, { useState } from "react";
import PropTypes from "prop-types";

import {
  Box,
  CircularProgress,
  Step,
  StepButton,
  Stepper,
  Typography,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  ButtonGroup,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import { TIMESTAMP_KEYS } from "../../constants/timestamp";
import TimestampWrapper from "../shared/TimestampWrapper";

import { useExplorationsContext, explorationModes } from "./context";
import { NameExplorationStep, ConfigureExplorersStep } from "./Steps";

import { useSnackbar } from "notistack";

import { createExploration, updateExploration } from "../../api/exploration";
import {
  createExplorer,
  deleteExplorer,
  updateExplorer,
} from "../../api/explorer";

const steps = [
  {
    name: "setNameAndDescription",
    label: "Set Name",
  },
  {
    name: "configureExplorers",
    label: "Configure Explorers",
  },
];

function ExplorationEditor({ open = false, handleCloseDialog = () => {} }) {
  const { explorationData, explorationMode } = useExplorationsContext();
  const { enqueueSnackbar } = useSnackbar();

  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("md"));
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));

  const [loading, setLoading] = useState(false);
  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);

  const submitExploration = async (exploration) => {
    switch (explorationMode) {
      case explorationModes.EXPLORATION_CREATE:
        return createExploration(
          exploration.dataset_id,
          exploration.name,
          exploration.description,
        );
      case explorationModes.EXPLORATION_EDIT:
        return updateExploration(
          exploration.id,
          exploration.name,
          exploration.description,
        );
      default:
        throw new Error("Unknown exploration mode");
    }
  };

  const submitExplorer = (explorer, exploration_id) => {
    switch (isNaN(explorer.id)) {
      case true:
        return createExplorer(
          exploration_id,
          explorer.columns,
          explorer.exploration_type,
          explorer.parameters,
          explorer.name,
        );
      case false:
        return updateExplorer(
          explorer.id,
          explorer.columns,
          explorer.parameters,
          explorer.name,
        );
      default:
        return new Promise.reject("Unknown error");
    }
  };

  const submitExplorers = async (explorers, exploration_id) => {
    return Promise.all(
      explorers.map((explorer) => submitExplorer(explorer, exploration_id)),
    );
  };

  const deleteExplorers = async (explorerIds) => {
    const createdExplorerIds = explorerIds.filter((id) => !isNaN(id));
    return Promise.all(createdExplorerIds.map((id) => deleteExplorer(id)));
  };

  const handleSubmit = () => {
    setLoading(true);
    submitExploration(explorationData)
      .then((data) => {
        submitExplorers(explorationData.explorers, data.id)
          .then(() => {
            deleteExplorers(explorationData.deleted_explorers)
              .then(() => {
                enqueueSnackbar("Exploration saved successfully", {
                  variant: "success",
                });
                handleCloseDialog();
              })
              .catch((error) => {
                enqueueSnackbar("Failed to delete explorers", {
                  variant: "error",
                });
                return;
              });
          })
          .catch((error) => {
            enqueueSnackbar("Failed to save explorers", { variant: "error" });
            return;
          });
      })
      .catch((error) => {
        enqueueSnackbar("Failed to save exploration", { variant: "error" });
        return;
      })
      .finally(() => {
        setLoading(false);
      });
  };

  const handleNextButton = () => {
    if (activeStep === steps.length - 1) {
      handleSubmit();
    } else {
      setActiveStep((prev) => prev + 1);
    }
  };

  const handleBackButton = () => {
    if (activeStep === 0) {
      handleCloseDialog();
    }

    setActiveStep((prev) => prev - 1);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  return (
    <Dialog
      open={open}
      fullScreen={screenSm}
      fullWidth
      maxWidth={"lg"}
      onClose={handleCloseDialog}
      aria-labelledby="new-exploration-dialog-title"
      aria-describedby="new-exploration-dialog-description"
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-exploration-dialog-title">
        <Grid container direction={"row"} alignItems={"center"}>
          <Grid item xs={12} md={3}>
            <Grid
              container
              direction="row"
              alignItems="center"
              justifyContent="space-between"
            >
              <Grid item xs={1}>
                <IconButton
                  edge="start"
                  color="inherit"
                  onClick={handleCloseDialog}
                  sx={{ display: { xs: "flex", sm: "none" } }}
                >
                  <CloseIcon />
                </IconButton>
              </Grid>
              <Grid item xs={11}>
                <Typography
                  variant="h6"
                  component="h3"
                  align={matches ? "center" : "left"}
                  sx={{ mb: { sm: 2, md: 0 } }}
                >
                  {explorationMode.title}
                </Typography>
              </Grid>
            </Grid>
          </Grid>
          <Grid item xs={12} md={9}>
            <Stepper
              nonLinear
              activeStep={activeStep}
              sx={{ maxWidth: "100%" }}
            >
              {steps.map((step, index) => (
                <Step
                  key={`${step.name}`}
                  completed={activeStep > index}
                  disabled={activeStep < index}
                >
                  <StepButton color="inherit" onClick={handleStepButton(index)}>
                    {step.label}
                  </StepButton>
                </Step>
              ))}
            </Stepper>
          </Grid>
        </Grid>
      </DialogTitle>

      {/* Main content - steps */}
      <DialogContent dividers>
        {loading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              height: "50vh",
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {!loading && activeStep === 0 && (
          <NameExplorationStep
            onValidation={(valid) => setNextEnabled(valid)}
          />
        )}

        {!loading && activeStep === 1 && (
          <ConfigureExplorersStep
            onValidation={(valid) => setNextEnabled(valid)}
          />
        )}
      </DialogContent>

      {/* Actions - Back and Next */}
      <DialogActions>
        <ButtonGroup size="large">
          <Button onClick={handleBackButton}>
            {activeStep === 0 ? "Close" : "Back"}
          </Button>
          <TimestampWrapper
            eventName={
              activeStep === 0
                ? TIMESTAMP_KEYS.exploration.configureExplorer
                : activeStep === 1
                ? TIMESTAMP_KEYS.exploration.submitExplorer
                : null
            }
          >
            <Button
              onClick={handleNextButton}
              autoFocus
              variant="contained"
              color="primary"
              disabled={!nextEnabled}
            >
              {activeStep === steps.length - 1 ? "Save" : "Next"}
            </Button>
          </TimestampWrapper>
        </ButtonGroup>
      </DialogActions>
    </Dialog>
  );
}

ExplorationEditor.propTypes = {
  open: PropTypes.bool,
  handleCloseDialog: PropTypes.func,
};

export default ExplorationEditor;
