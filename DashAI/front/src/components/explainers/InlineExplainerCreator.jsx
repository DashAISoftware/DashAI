import React, { useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  Step,
  StepLabel,
  Stepper,
  Typography,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { LoadingButton } from "@mui/lab";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";

import {
  createGlobalExplainer as createGlobalExplainerRequest,
  createLocalExplainer as createLocalExplainerRequest,
} from "../../api/explainer";
import { enqueueExplainerJob as enqueueExplainerJobRequest } from "../../api/job";
import { startJobPolling } from "../../utils/jobPoller";
import TimestampWrapper from "../shared/TimestampWrapper";
import { TIMESTAMP_KEYS } from "../../constants/timestamp";
import ConfigureExplainerStep from "./ConfigureExplainerStep";
import SelectDatasetStep from "./SelectDatasetStep";
import SetNameAndExplainerStep from "./SetNameAndExplainerStep";

const SNACKBAR_AUTO_HIDE_MS = 5000;

export default function InlineExplainerCreator({
  open,
  scope,
  explainerConfig,
  preselectedExplainer = null,
  onCreated,
  onCancel,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["explainers", "common"]);
  const formSubmitRef = useRef(null);

  const { runId, taskName, modelName } = explainerConfig;
  const isLocal = scope === "local";
  // With a preselected explainer the selection step is skipped entirely; the
  // stepper starts at dataset selection (local) or parameter configuration.
  const hasPreselected = Boolean(preselectedExplainer);

  const defaultNewExplainer = useMemo(
    () =>
      isLocal
        ? {
            run_id: runId,
            explainer_name: preselectedExplainer ?? null,
            scope: {
              mode: "split",
              split: "test",
              percentage: 20,
              shuffle: false,
            },
            dataset_id: null,
            parameters: null,
            fit_parameters: null,
            manual_input: null,
          }
        : {
            run_id: runId,
            explainer_name: preselectedExplainer ?? null,
            parameters: null,
          },
    [isLocal, runId, preselectedExplainer],
  );

  const steps = useMemo(() => {
    const stepLabels = [];
    if (!hasPreselected) {
      stepLabels.push(t("explainers:label.selectExplainer"));
    }
    if (isLocal) {
      stepLabels.push(t("explainers:label.selectDataset"));
    }
    stepLabels.push(t("explainers:label.configureExplainerParameters"));
    return stepLabels;
  }, [isLocal, hasPreselected, t]);

  const datasetStepIndex = hasPreselected ? 0 : 1;
  const configureStepIndex = (hasPreselected ? 0 : 1) + (isLocal ? 1 : 0);

  const [activeStep, setActiveStep] = useState(0);
  const [nextEnabled, setNextEnabled] = useState(false);
  const [newExpl, setNewExpl] = useState(defaultNewExplainer);
  const [isLoading, setIsLoading] = useState(false);

  const resetState = () => {
    setActiveStep(0);
    setNewExpl(defaultNewExplainer);
    setNextEnabled(false);
  };

  useEffect(() => {
    if (!open) resetState();
  }, [open]);

  const enqueueExplainerJob = async (explainerId) => {
    try {
      const manualInput =
        isLocal && newExpl.scope?.mode === "manual"
          ? newExpl.manual_input
          : undefined;
      const response = await enqueueExplainerJobRequest(
        explainerId,
        scope,
        manualInput,
      );
      enqueueSnackbar(
        t(
          isLocal
            ? "explainers:message.localExplainerJobCreated"
            : "explainers:message.globalExplainerJobCreated",
        ),
        { variant: "success", autoHideDuration: SNACKBAR_AUTO_HIDE_MS },
      );

      if (response && response.id) {
        startJobPolling(
          response.id,
          () => {
            enqueueSnackbar(
              t("explainers:message.explainerJobCompleted", {
                name: newExpl.name,
              }),
              { variant: "success", autoHideDuration: SNACKBAR_AUTO_HIDE_MS },
            );
            if (onCreated) onCreated();
          },
          (result) => {
            console.error(`${scope} explainer job failed:`, result);
            enqueueSnackbar(
              t(
                isLocal
                  ? "explainers:error.localExplainerJobFailed"
                  : "explainers:error.globalExplainerJobFailed",
                { error: result.error || "Unknown error" },
              ),
              { variant: "error", autoHideDuration: SNACKBAR_AUTO_HIDE_MS },
            );
            if (onCreated) onCreated();
          },
        );
      }

      return response;
    } catch (error) {
      enqueueSnackbar(
        t(
          isLocal
            ? "explainers:error.localExplainerJobEnqueueError"
            : "explainers:error.globalExplainerJobEnqueueError",
        ),
        { variant: "error", autoHideDuration: SNACKBAR_AUTO_HIDE_MS },
      );
      console.error("Error details:", error);
      throw error;
    }
  };

  const uploadNewExplainer = async () => {
    try {
      setIsLoading(true);

      const response = isLocal
        ? await createLocalExplainerRequest(
            newExpl.run_id,
            newExpl.explainer_name,
            newExpl.dataset_id,
            newExpl.parameters,
            newExpl.fit_parameters,
            newExpl.scope,
          )
        : await createGlobalExplainerRequest(
            newExpl.run_id,
            newExpl.explainer_name,
            newExpl.parameters,
          );

      await enqueueExplainerJob(response.id);
      if (onCreated) onCreated();
      return true;
    } catch (error) {
      enqueueSnackbar(
        t(
          isLocal
            ? "explainers:error.localExplainerCreationError"
            : "explainers:error.globalExplainerCreationError",
        ),
        { variant: "error", autoHideDuration: SNACKBAR_AUTO_HIDE_MS },
      );
      console.error("Error details:", error);
      return false;
    } finally {
      setIsLoading(false);
    }
  };

  const handleBack = () => {
    setActiveStep((prev) => prev - 1);
    setNextEnabled(true);
  };

  const handleNext = async () => {
    if (activeStep < steps.length - 1) {
      setActiveStep((prev) => prev + 1);
      setNextEnabled(false);
      return;
    }

    const isSuccess = await uploadNewExplainer();
    if (isSuccess) {
      resetState();
      onCancel();
    }
  };

  return (
    <Dialog
      open={open}
      onClose={onCancel}
      maxWidth="lg"
      fullWidth
      PaperProps={{
        sx: { minHeight: "500px" },
      }}
    >
      <DialogTitle sx={{ bgcolor: "background.paper" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
          }}
        >
          <Typography variant="h6" component="span">
            {t(
              isLocal
                ? "explainers:label.newLocalExplainer"
                : "explainers:label.newGlobalExplainer",
            )}
            {hasPreselected ? `: ${preselectedExplainer}` : ""}
          </Typography>
          <IconButton
            onClick={onCancel}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Stepper activeStep={activeStep} sx={{ mb: 3 }}>
          {steps.map((label) => (
            <Step key={label} completed={false}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {!hasPreselected && activeStep === 0 && (
          <SetNameAndExplainerStep
            newExpl={newExpl}
            setNewExpl={setNewExpl}
            setNextEnabled={setNextEnabled}
            scope={isLocal ? "Local" : "Global"}
            taskName={taskName}
            modelName={modelName}
          />
        )}
        {isLocal && activeStep === datasetStepIndex && (
          <SelectDatasetStep
            newExpl={newExpl}
            setNewExpl={setNewExpl}
            setNextEnabled={setNextEnabled}
          />
        )}
        {activeStep === configureStepIndex && (
          <ConfigureExplainerStep
            newExpl={newExpl}
            setNewExpl={setNewExpl}
            setNextEnabled={setNextEnabled}
            formSubmitRef={formSubmitRef}
            scope={isLocal ? "Local" : "global"}
          />
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        {activeStep > 0 && (
          <Button variant="outlined" onClick={handleBack} disabled={isLoading}>
            {t("common:back")}
          </Button>
        )}
        <TimestampWrapper
          eventName={
            activeStep === steps.length - 1
              ? isLocal
                ? TIMESTAMP_KEYS.explainer.submitLocal
                : TIMESTAMP_KEYS.explainer.submitGlobal
              : null
          }
        >
          <LoadingButton
            onClick={handleNext}
            variant="contained"
            color="primary"
            disabled={!nextEnabled || isLoading}
            loading={isLoading}
          >
            {activeStep === steps.length - 1
              ? t("common:save")
              : t("common:next")}
          </LoadingButton>
        </TimestampWrapper>
      </DialogActions>
    </Dialog>
  );
}

InlineExplainerCreator.propTypes = {
  open: PropTypes.bool.isRequired,
  scope: PropTypes.oneOf(["global", "local"]).isRequired,
  explainerConfig: PropTypes.shape({
    runId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
    taskName: PropTypes.string,
    modelName: PropTypes.string,
  }).isRequired,
  preselectedExplainer: PropTypes.string,
  onCreated: PropTypes.func,
  onCancel: PropTypes.func.isRequired,
};
