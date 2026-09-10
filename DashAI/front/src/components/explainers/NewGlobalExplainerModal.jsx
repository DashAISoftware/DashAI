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
import { startJobPolling } from "../../utils/jobPoller";

import {
  createGlobalExplainer as createGlobalExplainerRequest,
  getExplainers,
} from "../../api/explainer";
import { enqueueExplainerJob as enqueueExplainerJobRequest } from "../../api/job";

import ConfigureExplainerStep from "./ConfigureExplainerStep";
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
    base: "Explainer_global",
    items: existingExplainers,
    getName: (explainer) => explainer?.name,
  });

  return defaultName;
};

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
      name: "configureExplainer",
      label: t("explainers:label.configureExplainerParameters"),
    },
  ];

  const { enqueueSnackbar } = useSnackbar();

  const { runId, taskName, modelName } = explainerConfig;

  const defaultNewGlobalExpl = {
    name: "",
    run_id: runId,
    explainer_name: null,
    parameters: null,
  };

  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newGlobalExpl, setNewGlobalExpl] = useState(defaultNewGlobalExpl);
  const [existingGlobalExplainers, setExistingGlobalExplainers] = useState([]);
  const [existingGlobalExplainersLoaded, setExistingGlobalExplainersLoaded] =
    useState(false);

  const [isLoading, setIsLoading] = useState(false);

  const { updateFlag: updateExplainers } = useUpdateFlag({
    flag: flags.EXPLAINERS,
  });

  const loadExistingExplainers = async () => {
    try {
      const explainers = await getExplainers(undefined, "global");
      setExistingGlobalExplainers(explainers);
    } catch (error) {
      console.error("Error loading existing explainers:", error);
      setExistingGlobalExplainers([]);
    } finally {
      setExistingGlobalExplainersLoaded(true);
    }
  };

  useEffect(() => {
    if (open) {
      setExistingGlobalExplainersLoaded(false);
      loadExistingExplainers();
    }
  }, [open]);

  useEffect(() => {
    if (!open || !existingGlobalExplainersLoaded || newGlobalExpl.name.trim()) {
      return;
    }

    setNewGlobalExpl((prev) => ({
      ...prev,
      name: getNextExplainerName(existingGlobalExplainers),
    }));
  }, [
    open,
    existingGlobalExplainersLoaded,
    existingGlobalExplainers,
    newGlobalExpl.name,
  ]);

  const enqueueGlobalExplainerJob = async (explainerId) => {
    try {
      const response = await enqueueExplainerJobRequest(explainerId, "global");
      enqueueSnackbar(t("explainers:message.globalExplainerJobCreated"), {
        variant: "success",
      });

      if (response && response.id) {
        startJobPolling(
          response.id,
          (result) => {
            enqueueSnackbar(
              t("explainers:message.explainerJobCompleted", {
                name: newGlobalExpl.name,
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
            console.error("Global explainer job failed:", result);
            enqueueSnackbar(
              t("explainers:error.globalExplainerJobFailed", {
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
      enqueueSnackbar(t("explainers:error.globalExplainerJobEnqueueError"), {
        variant: "error",
      });
      console.error("Error details:", error);
      throw error;
    }
  };

  const uploadNewGlobalExplainer = async () => {
    try {
      setIsLoading(true);
      const response = await createGlobalExplainerRequest(
        newGlobalExpl.name,
        newGlobalExpl.run_id,
        newGlobalExpl.explainer_name,
        newGlobalExpl.parameters,
      );
      const explainerId = response.id;
      await enqueueGlobalExplainerJob(explainerId);
      await loadExistingExplainers();
    } catch (error) {
      enqueueSnackbar(t("explainers:error.globalExplainerCreationError"), {
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

  const handleNextButton = async () => {
    if (activeStep < steps.length - 1) {
      setActiveStep(activeStep + 1);
      setNextEnabled(false);
    } else {
      await uploadNewGlobalExplainer();
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
      aria-labelledby="new-global-explainer-dialog-title"
      aria-describedby="new-global-explainer-dialog-description"
      scroll="paper"
      slotProps={{
        paper: {
          sx: { minHeight: "80vh" },
        },
      }}
    >
      {/* Title */}
      <DialogTitle id="new-global-explainer-dialog-title">
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
                  {t("explainers:label.newGlobalExplainer")}
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
            newExpl={newGlobalExpl}
            setNewExpl={setNewGlobalExpl}
            setNextEnabled={setNextEnabled}
            scope={"Global"}
            taskName={taskName}
            modelName={modelName}
            existingExplainers={existingGlobalExplainers}
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
        <Button variant="outlined" onClick={handleBackButton}>
          {activeStep === 0 ? t("common:close") : t("common:back")}
        </Button>
        <TimestampWrapper
          eventName={
            activeStep === 1 ? TIMESTAMP_KEYS.explainer.submitGlobal : null
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

NewGlobalExplainerModal.propTypes = {
  open: PropTypes.bool.isRequired,
  setOpen: PropTypes.func.isRequired,
  explainerConfig: PropTypes.object,
};
