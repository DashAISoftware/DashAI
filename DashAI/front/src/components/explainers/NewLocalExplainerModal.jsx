import React, { useEffect, useState, useRef } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stepper,
  Step,
  StepButton,
  Grid,
  Typography,
  IconButton,
  Box,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTheme } from "@mui/material/styles";
import useMediaQuery from "@mui/material/useMediaQuery";

import { createLocalExplainer as createLocalExplainerRequest } from "../../api/explainer";
import { enqueueExplainerJob as enqueueExplainerJobRequest } from "../../api/job";
import { getExplainers } from "../../api/explainer";

import { startJobPolling } from "../../utils/jobPoller";
import ConfigureExplainerStep from "./ConfigureExplainerStep";
import SelectDatasetStep from "./SelectDatasetStep";
import SetNameAndExplainerStep from "./SetNameAndExplainerStep";
import useUpdateFlag from "../../hooks/useUpdateFlag";
import { flags } from "../../constants/flags";
import TimestampWrapper from "../shared/TimestampWrapper";
import { TIMESTAMP_KEYS } from "../../constants/timestamp";
import { LoadingButton } from "@mui/lab";
import { useTranslation } from "react-i18next";
import { generateSequentialName } from "../../utils/nameGenerator";

const getNextExplainerName = (existingExplainers = []) => {
  const { defaultName } = generateSequentialName({
    base: "Explainer_local",
    items: existingExplainers,
    getName: (explainer) => explainer?.name,
  });

  return defaultName;
};

/**
 * This component renders a modal that takes the user through the process of creating a new experiment.
 * @param {bool} open true to open the modal, false to close it
 * @param {function} setOpen function to modify the value of open
 * @param {function} updateExperiments function to update the experiments table
 */
export default function NewLocalExplainerModal({
  open,
  setOpen,
  explainerConfig,
  onExplainerCreated,
}) {
  const theme = useTheme();
  const matches = useMediaQuery(theme.breakpoints.down("md"));
  const screenSm = useMediaQuery(theme.breakpoints.down("sm"));
  const formSubmitRef = useRef(null);
  const { t } = useTranslation(["explainers", "common"]);
  const steps = [
    {
      name: "selectExplainer",
      label: t("explainers:label.selectExplainer"),
    },
    {
      name: "selectDataset",
      label: t("explainers:label.selectDataset"),
    },
    {
      name: "configureExplainer",
      label: t("explainers:label.configureExplainerParameters"),
    },
  ];

  const { enqueueSnackbar } = useSnackbar();

  const { runId, taskName, modelName } = explainerConfig;

  const defaultNewLocalExpl = {
    name: "",
    run_id: runId,
    explainer_name: null,
    scope: { split: "test", percentage: 20 },
    dataset_id: null,
    parameters: null,
    fit_parameters: null,
  };

  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newLocalExpl, setNewLocalExpl] = useState(defaultNewLocalExpl);
  const [existingLocalExplainers, setExistingLocalExplainers] = useState([]);
  const [existingLocalExplainersLoaded, setExistingLocalExplainersLoaded] =
    useState(false);
  const [isLoading, setIsLoading] = useState(false);

  const { updateFlag: updateExplainers } = useUpdateFlag({
    flag: flags.EXPLAINERS,
  });

  const loadExistingExplainers = async () => {
    try {
      const explainers = await getExplainers(undefined, "local");
      setExistingLocalExplainers(explainers);
    } catch (error) {
      console.error("Error loading existing explainers:", error);
      setExistingLocalExplainers([]);
    } finally {
      setExistingLocalExplainersLoaded(true);
    }
  };

  useEffect(() => {
    if (open) {
      setExistingLocalExplainersLoaded(false);
      loadExistingExplainers();
    }
  }, [open]);

  useEffect(() => {
    if (!open || !existingLocalExplainersLoaded || newLocalExpl.name.trim()) {
      return;
    }

    setNewLocalExpl((prev) => ({
      ...prev,
      name: getNextExplainerName(existingLocalExplainers),
    }));
  }, [
    open,
    existingLocalExplainersLoaded,
    existingLocalExplainers,
    newLocalExpl.name,
  ]);

  const enqueueLocalExplainerJob = async (explainerId) => {
    try {
      const response = await enqueueExplainerJobRequest(explainerId, "local");
      enqueueSnackbar(t("explainers:message.localExplainerJobCreated"), {
        variant: "success",
      });

      // Start tracking this job
      if (response && response.id) {
        startJobPolling(
          response.id,
          (result) => {
            enqueueSnackbar(
              t("explainers:message.explainerJobCompleted", {
                name: newLocalExpl.name,
              }),
              {
                variant: "success",
              },
            );
            updateExplainers();
            if (onExplainerCreated) {
              onExplainerCreated();
            }
          },
          (result) => {
            console.error("Local explainer job failed:", result);
            enqueueSnackbar(
              t("explainers:error.localExplainerJobFailed", {
                error: result.error || "Unknown error",
              }),
              { variant: "error" },
            );
            updateExplainers();
            if (onExplainerCreated) {
              onExplainerCreated();
            }
          },
        );
      }

      return response;
    } catch (error) {
      enqueueSnackbar(t("explainers:error.localExplainerJobEnqueueError"));
      console.error("Error details:", error);
      throw error;
    }
  };

  const uploadNewLocalExplainer = async () => {
    try {
      setIsLoading(true);
      const response = await createLocalExplainerRequest(
        newLocalExpl.name,
        newLocalExpl.run_id,
        newLocalExpl.explainer_name,
        newLocalExpl.dataset_id,
        newLocalExpl.parameters,
        newLocalExpl.fit_parameters,
        newLocalExpl.scope,
      );
      const explainerId = response.id;
      await enqueueLocalExplainerJob(explainerId);
      await loadExistingExplainers();
    } catch (error) {
      enqueueSnackbar(t("explainers:error.localExplainerCreationError"), {
        variant: "error",
      });
      console.error("Error details:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleCloseDialog = () => {
    setActiveStep(0);
    setOpen(false);
    setNewLocalExpl(defaultNewLocalExpl);
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

  const handleNextButton = async () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      await uploadNewLocalExplainer();
      handleCloseDialog();
    }
  };

  return (
    <Dialog
      open={open}
      fullScreen={screenSm}
      fullWidth
      maxWidth={"lg"}
      onClose={() => {}}
      disableEscapeKeyDown
      aria-labelledby="new-local-explainer-dialog-title"
      aria-describedby="new-local-explainer-dialog-description"
      scroll="paper"
      slotProps={{
        paper: {
          sx: { minHeight: "80vh" },
        },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-local-explainer-dialog-title">
        <Grid container direction={"row"} alignItems={"center"}>
          <Grid size={{ xs: 12, md: 3 }}>
            <Grid
              container
              direction="row"
              alignItems="center"
              justifyContent="space-between"
            >
              <Grid size={{ xs: 1 }}>
                <IconButton
                  edge="start"
                  color="inherit"
                  onClick={handleCloseDialog}
                  sx={{ display: { xs: "flex", sm: "none" } }}
                >
                  <CloseIcon />
                </IconButton>
              </Grid>
              <Grid size={{ xs: 11 }}>
                <Typography
                  variant="h6"
                  component="h3"
                  align={matches ? "center" : "left"}
                  sx={{ mb: { sm: 2, md: 0 } }}
                >
                  {t("explainers:label.newLocalExplainer")}
                </Typography>
              </Grid>
            </Grid>
          </Grid>
          <Grid size={{ xs: 12, md: 8 }}>
            <Stepper
              nonLinear
              activeStep={activeStep}
              sx={{ maxWidth: "100%" }}
            >
              {steps.map((step, index) => (
                <Step
                  key={`${step.name}`}
                  completed={false}
                  disabled={activeStep < index}
                >
                  <StepButton color="inherit" onClick={handleStepButton(index)}>
                    {step.label}
                  </StepButton>
                </Step>
              ))}
            </Stepper>
          </Grid>
          <Grid
            size={{ xs: 12, md: 1 }}
            sx={{
              display: { xs: "none", sm: "flex" },
              justifyContent: "flex-end",
            }}
          >
            <IconButton
              onClick={handleCloseDialog}
              sx={{
                color: (theme) => theme.palette.grey[500],
              }}
            >
              <CloseIcon />
            </IconButton>
          </Grid>
        </Grid>
      </DialogTitle>
      {/* Main content - steps */}
      <DialogContent dividers>
        {activeStep === 0 && (
          <SetNameAndExplainerStep
            newExpl={newLocalExpl}
            setNewExpl={setNewLocalExpl}
            setNextEnabled={setNextEnabled}
            scope={"Local"}
            taskName={taskName}
            modelName={modelName}
            existingExplainers={existingLocalExplainers}
          />
        )}
        {activeStep === 1 && (
          <SelectDatasetStep
            newExpl={newLocalExpl}
            setNewExpl={setNewLocalExpl}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === 2 && (
          <ConfigureExplainerStep
            newExpl={newLocalExpl}
            setNewExpl={setNewLocalExpl}
            setNextEnabled={setNextEnabled}
            formSubmitRef={formSubmitRef}
            scope={"Local"}
          />
        )}
      </DialogContent>
      {/* Actions - Back and Next */}
      <DialogActions>
        <Button variant="outlined" onClick={handleBackButton}>
          {activeStep === 0 ? t("common:close") : t("common:back")}
        </Button>
        <TimestampWrapper
          eventName={
            activeStep === 1 ? TIMESTAMP_KEYS.explainer.submitLocal : null
          }
        >
          <LoadingButton
            onClick={handleNextButton}
            autoFocus
            variant="contained"
            color="primary"
            disabled={!nextEnabled}
            loading={isLoading}
          >
            {activeStep === 1 ? t("common:save") : t("common:next")}
          </LoadingButton>
        </TimestampWrapper>
      </DialogActions>
    </Dialog>
  );
}

NewLocalExplainerModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  explainerConfig: PropTypes.object,
};
