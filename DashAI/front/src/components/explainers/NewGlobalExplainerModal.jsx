import React, { useState, useRef } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  ButtonGroup,
  Stepper,
  Step,
  StepButton,
  Grid,
  Typography,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import { createGlobalExplainer as createGlobalExplainerRequest } from "../../api/explainer";
import { enqueueExplainerJob as enqueueExplainerJobRequest } from "../../api/job";

import ConfigureExplainerStep from "./ConfigureExplainerStep";
import SetNameAndExplainerStep from "./SetNameAndExplainerStep";

const steps = [
  { name: "selectExplainer", label: "Set name and explainer" },
  { name: "configureExplainer", label: "Configure explainer" },
];

/**
 * This component renders a modal that takes the user through the process of creating a new explainer.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {object} explainerConfig
 */
export default function NewGlobalExplainerModal({
  open,
  setOpen,
  explainerConfig,
}) {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("md"));
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));
  const formSubmitRef = useRef(null);

  const { enqueueSnackbar } = useSnackbar();

  const { runId } = explainerConfig;

  const defaultNewGlobalExpl = {
    name: "",
    run_id: runId,
    explainer_name: null,
    parameters: null,
  };

  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newGlobalExpl, setNewGlobalExpl] = useState(defaultNewGlobalExpl);

  const enqueueGlobalExplainerJob = async (explainerId) => {
    try {
      await enqueueExplainerJobRequest(explainerId, "global");
      enqueueSnackbar("Global explainer job successfully created.", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error while trying to enqueue global explainer job");
      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const uploadNewGlobalExplainer = async () => {
    try {
      const response = await createGlobalExplainerRequest(
        newGlobalExpl.name,
        newGlobalExpl.run_id,
        newGlobalExpl.explainer_name,
        newGlobalExpl.parameters,
      );
      const explainerId = response.id;
      await enqueueGlobalExplainerJob(explainerId);
      enqueueSnackbar("Global explainer successfully created.", {
        variant: "success",
      });
    } catch (error) {
      enqueueSnackbar("Error while trying to create a new explainer");

      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }
    }
  };

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
    setNewGlobalExpl(defaultNewGlobalExpl);
    setNextEnabled(false);
  };

  const handleStepButton = (stepIndex) => () => {
    setActiveStep(stepIndex);
  };

  const handleBackButton = () => {
    if (activeStep === 0) {
      handleCloseDialog();
    } else {
      setActiveStep(activeStep - 1);
    }
  };

  const handleNextButton = () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      formSubmitRef.current.handleSubmit();
      uploadNewGlobalExplainer();
      handleCloseDialog();
    }
  };

  return (
    <Dialog
      open={open}
      fullScreen={screenSm}
      fullWidth
      maxWidth={"lg"}
      onClose={handleCloseDialog}
      aria-labelledby="new-global-explainer-dialog-title"
      aria-describedby="new-global-explainer-dialog-description"
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-global-explainer-dialog-title">
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
                  New global explainer
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
        {activeStep === 0 && (
          <SetNameAndExplainerStep
            newExpl={newGlobalExpl}
            setNewExpl={setNewGlobalExpl}
            setNextEnabled={setNextEnabled}
            scope={"Global"}
          />
        )}
        {activeStep === 1 && (
          <ConfigureExplainerStep
            newExpl={newGlobalExpl}
            setNewExpl={setNewGlobalExpl}
            setNextEnabled={setNextEnabled}
            scope={"global"}
            formSubmitRef={formSubmitRef}
          />
        )}
      </DialogContent>

      {/* Actions - Back and Next */}
      <DialogActions>
        <ButtonGroup size="large">
          <Button onClick={handleBackButton}>
            {activeStep === 0 ? "Close" : "Back"}
          </Button>
          <Button
            onClick={handleNextButton}
            autoFocus
            variant="contained"
            color="primary"
            disabled={!nextEnabled}
          >
            {activeStep === 1 ? "Save" : "Next"}
          </Button>
        </ButtonGroup>
      </DialogActions>
    </Dialog>
  );
}

NewGlobalExplainerModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  explainerConfig: PropTypes.object,
};
