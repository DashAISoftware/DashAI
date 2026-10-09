import React, { useEffect, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  Alert,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import RetrainConfirmDialog from "./RetrainConfirmDialog";
import RunEditForm from "./RunEditForm";
import useRunEditForm from "../../hooks/useRunEditForm";

/**
 * Editable-parameters dialog for a run — the same form used to configure it
 * before training, pre-filled with its current values. Shared by RunCard's
 * "Editar" button and the compact model card's quick-edit action so both
 * entry points open the exact same modal.
 *
 * Same two-step Stepper pattern as AddModelDialog: a second "Configure
 * Optimizer" step only appears once a parameter is marked for optimization.
 */
export default function RunEditDialog({
  run,
  session,
  existingRuns = [],
  onRefresh,
  open,
  onClose,
}) {
  const { t } = useTranslation(["models", "common"]);
  const [activeStep, setActiveStep] = useState(0);

  const formProps = useRunEditForm({
    run,
    session,
    existingRuns,
    onRefresh,
    onSaved: onClose,
    enabled: open,
  });

  const {
    canSave,
    hasOptimizableParams,
    validateBasics,
    operationsCount,
    isSaving,
    saveConfirmOpen,
    setSaveConfirmOpen,
    doSave,
    handleSaveEdit,
  } = formProps;

  // Always start on the first step when the dialog (re)opens.
  useEffect(() => {
    if (open) setActiveStep(0);
  }, [open]);

  const steps = hasOptimizableParams
    ? [t("models:label.configureModel"), t("models:label.configureOptimizer")]
    : [t("models:label.configureModel")];
  const isLastStep = activeStep === steps.length - 1;

  const handleNext = () => {
    if (!validateBasics()) return;
    setActiveStep(1);
  };

  const handleBack = () => {
    if (activeStep > 0) setActiveStep(activeStep - 1);
  };

  const handlePrimaryAction = () => {
    if (isLastStep) {
      handleSaveEdit();
    } else {
      handleNext();
    }
  };

  return (
    <>
      <Dialog
        open={open}
        onClose={onClose}
        maxWidth="md"
        fullWidth
        PaperProps={{ sx: { minHeight: "500px" } }}
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
              {t("models:label.editRun")}
            </Typography>
            <IconButton
              size="small"
              onClick={onClose}
              sx={{ color: "text.secondary" }}
            >
              <CloseIcon />
            </IconButton>
          </Box>
        </DialogTitle>

        <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
          <Alert severity="info" sx={{ mb: 6 }}>
            {t("models:message.editingParametersWarning")}
          </Alert>

          <Stepper activeStep={activeStep} sx={{ mb: 6 }}>
            {steps.map((label) => (
              <Step key={label} completed={false}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          <RunEditForm run={run} activeStep={activeStep} {...formProps} />
        </DialogContent>

        <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
          <Button variant="outlined" onClick={onClose} disabled={isSaving}>
            {t("common:cancel")}
          </Button>
          {activeStep > 0 && (
            <Button variant="outlined" onClick={handleBack} disabled={isSaving}>
              {t("common:back")}
            </Button>
          )}
          <Button
            variant="contained"
            onClick={handlePrimaryAction}
            disabled={
              isSaving || (isLastStep ? !canSave : !formProps.editedName.trim())
            }
          >
            {isLastStep
              ? isSaving
                ? t("common:saving")
                : t("common:save")
              : t("common:next")}
          </Button>
        </DialogActions>
      </Dialog>

      <RetrainConfirmDialog
        mode="save"
        open={saveConfirmOpen}
        onClose={() => setSaveConfirmOpen(false)}
        onConfirm={doSave}
        run={run}
        operationsCount={operationsCount}
      />
    </>
  );
}

RunEditDialog.propTypes = {
  run: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    model_name: PropTypes.string,
    parameters: PropTypes.object,
    optimizer_name: PropTypes.string,
    optimizer_parameters: PropTypes.object,
    goal_metric: PropTypes.string,
  }).isRequired,
  session: PropTypes.shape({
    task_name: PropTypes.string,
  }),
  existingRuns: PropTypes.array,
  onRefresh: PropTypes.func,
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
};
