import React, { useState } from "react";
import PropTypes from "prop-types";

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

import { createExperiment as createExperimentRequest } from "../../api/experiment";
import { createRun as createRunRequest } from "../../api/run";

import SetNameAndTaskStep from "./SetNameAndTaskStep";
import SelectDatasetStep from "./SelectDatasetStep";
import PrepareDatasetStep from "./PrepareDatasetStep";
import ConfigureModelsStep from "./ConfigureModelsStep";

import { useSnackbar } from "notistack";

const steps = [
  { name: "selectTask", label: "Set name and task" },
  { name: "selectDataset", label: "Select dataset" },
  { name: "prepareDataset", label: "Prepare dataset" },
  { name: "configureModels", label: "Configure models" },
];

const defaultNewExp = {
  id: "",
  name: "",
  dataset: null,
  task_name: "",
  input_columns: [],
  output_columns: [],
  splits: {
    has_changed: false,
    is_random: true,
    training: 70,
    validation: 10,
    testing: 20,
  },
  step: "SET_NAME",
  created: null,
  last_modified: null,
  runs: [],
};
/**
 * This component renders a modal that takes the user through the process of creating a new experiment.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {function} updateExperiments function to update the experiments table
 */
export default function NewExperimentModal({
  open,
  setOpen,
  updateExperiments,
}) {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("md"));
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));
  const { enqueueSnackbar } = useSnackbar();

  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newExp, setNewExp] = useState(defaultNewExp);

  const uploadRuns = async (experimentId) => {
    for (const run of newExp.runs) {
      try {
        await createRunRequest(
          experimentId,
          run.model,
          run.name,
          run.params,
          "",
        );
      } catch (error) {
        enqueueSnackbar(`Error while trying to create a new run: ${run.name}`);

        if (error.response) {
          console.error("Response error:", error.message);
        } else if (error.request) {
          console.error("Request error", error.request);
        } else {
          console.error("Unknown Error", error.message);
        }
      }
    }
  };

  const uploadNewExperiment = async () => {
    try {
      const response = await createExperimentRequest(
        newExp.dataset.id,
        newExp.task_name,
        newExp.name,
        newExp.input_columns,
        newExp.output_columns,
        JSON.stringify(newExp.splits),
      );
      const experimentId = response.id;
      await uploadRuns(experimentId);

      enqueueSnackbar("Experiment successfully created.", {
        variant: "success",
      });
      updateExperiments();
    } catch (error) {
      enqueueSnackbar("Error while trying to create a new experiment");

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
    setNewExp(defaultNewExp);
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
      uploadNewExperiment();
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
      aria-labelledby="new-experiment-dialog-title"
      aria-describedby="new-experiment-dialog-description"
      scroll="paper"
      PaperProps={{
        sx: { minHeight: "80vh" },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-experiment-dialog-title">
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
                  New experiment
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
          <SetNameAndTaskStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 1 && (
          <SelectDatasetStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 2 && (
          <PrepareDatasetStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 3 && (
          <ConfigureModelsStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
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
            {activeStep === 3 ? "Save" : "Next"}
          </Button>
        </ButtonGroup>
      </DialogActions>
    </Dialog>
  );
}

NewExperimentModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  updateExperiments: PropTypes.func.isRequired,
};
