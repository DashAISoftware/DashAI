import { useStrategyKind } from "../../hooks/useStrategyKind";
import { STRATEGY_KINDS } from "../../utils/splitsPayload";
import React, { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Stepper,
  Step,
  StepLabel,
  TextField,
  Box,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { useSnackbar } from "notistack";
import FormSchemaWithSelectedModel from "../shared/FormSchemaWithSelectedModel";
import FormSchemaContainer from "../shared/FormSchemaContainer";
import OptimizationTableSelectOptimizer from "./modelSession/OptimizationTableSelectOptimizer";
import ModelsTableSelectMetric from "./modelSession/ModelsTableSelectMetric";
import NestedCVSelector from "./modelSession/NestedCVSelector";
import useSchema from "../../hooks/useSchema";
import { generateSequentialName } from "../../utils/nameGenerator";
import { createRun } from "../../api/run";
import { getRequiredDownloads } from "../../api/component";
import { subscribeAnyDownloadState } from "./model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import { useTranslation } from "react-i18next";
import { useTourContext } from "../tour/TourProvider";
import { checkIfHaveOptimazers } from "../../utils/schema";
import { getDatasetInfo } from "../../api/datasets";
import { useModels } from "./ModelsContext";

const DEFAULT_INNER_CONFIG = {
  splitterType: null, // null means: derive from outer splitter on mount
  nSplits: 2,
};

/**
 * Dialog for adding a new model run to a session
 * Step 1: Configure model name and parameters
 * Step 2: Configure optimizer for train
 */
function AddModelDialog({
  open,
  onClose,
  session,
  preselectedModel,
  preselectedModelObject,
  existingRuns = [],
  onRunCreated,
}) {
  const { enqueueSnackbar } = useSnackbar();
  // Nested cross-validation only applies to a folded strategy, which the
  // backend reports rather than the strategy name implying it.
  const isCrossValidation =
    useStrategyKind(session?.evaluation_strategy) === STRATEGY_KINDS.CV;

  const [activeStep, setActiveStep] = useState(0);
  const [name, setName] = useState("");
  const [selectedModel, setSelectedModel] = useState(preselectedModel || "");
  const [modelParameters, setModelParameters] = useState({});
  const [selectedOptimizer, setSelectedOptimizer] = useState("");
  const [optimizerParameters, setOptimizerParameters] = useState({});
  const [loading, setLoading] = useState(false);
  const [hasUserTouchedName, setHasUserTouchedName] = useState(false);
  const [goalMetric, setGoalMetric] = useState("");
  const [hasLoadedInitialParams, setHasLoadedInitialParams] = useState(false);
  const [useNestedCV, setUseNestedCV] = useState(false);
  const [innerConfig, setInnerConfig] = useState(DEFAULT_INNER_CONFIG);
  const [totalRows, setTotalRows] = useState(null);
  const [modelDownloaded, setModelDownloaded] = useState(true);
  const [missingNested, setMissingNested] = useState([]);
  const { datasetRowCount } = useModels();
  const { t } = useTranslation(["models", "common", "credentials"]);

  // The model can only be trained once its required credentials are
  // authenticated. Derived from the live credential store so it reacts the
  // moment a credential is verified in the dialog.
  const { statuses, loaded } = useCredentialStatuses();
  const { locked: credentialsLocked, requiredPlatforms } =
    getComponentCredentialState(preselectedModelObject || {}, statuses, loaded);

  const { defaultValues: defaultModelParams } = useSchema({
    modelName: open ? selectedModel : null,
  });
  // Fetched as soon as the dialog opens (not gated on activeStep === 1) so it
  // has the whole step-1 dwell time to resolve before the user reaches step 2
  // — otherwise the "Parámetros del Optimizador" section briefly renders
  // empty right after clicking "Siguiente", shrinking the dialog for a beat.
  const {
    defaultValues: defaultOptimizerParams,
    loading: optimizerSchemaLoading,
  } = useSchema({
    modelName: open ? selectedOptimizer : null,
  });

  const tourContext = useTourContext();

  const outerSplit = useMemo(() => {
    return session?.splits ? JSON.parse(session.splits) : null;
  }, [session?.splits]);

  useEffect(() => {
    if (open && selectedModel) {
      const generated = generateSequentialName({
        base: selectedModel,
        items: existingRuns,
        getName: (run) => run.name,
        filter: (run) => run.model_name === selectedModel,
      });
      if (!hasUserTouchedName) {
        setName(generated.defaultName);
      }
    }
  }, [open, selectedModel, existingRuns, hasUserTouchedName]);

  const hasOptimizableParams = useMemo(() => {
    return checkIfHaveOptimazers(modelParameters);
  }, [modelParameters]);

  const steps = hasOptimizableParams
    ? [t("models:label.configureModel"), t("models:label.configureOptimizer")]
    : [t("models:label.configureModel")];

  useEffect(() => {
    if (preselectedModel && preselectedModel !== selectedModel) {
      setSelectedModel(preselectedModel);
      setModelParameters({});
      setHasUserTouchedName(false);
      setHasLoadedInitialParams(false);
    }
  }, [preselectedModel, selectedModel]);

  useEffect(() => {
    const comp = preselectedModelObject;
    const requiresDownload = Boolean(comp?.metadata?.requires_download);
    const isDownloaded = Boolean(comp?.downloaded);
    setModelDownloaded(!requiresDownload || isDownloaded);
  }, [preselectedModelObject]);

  // Block advancing while any component selected inside the model parameters
  // still needs downloading. The check walks the nested parameters server-side
  // and re-runs after an inline download/delete finishes anywhere.
  useEffect(() => {
    if (
      !open ||
      activeStep !== 0 ||
      !modelParameters ||
      Object.keys(modelParameters).length === 0
    ) {
      setMissingNested([]);
      return;
    }
    let cancelled = false;
    const check = async () => {
      try {
        const missing = await getRequiredDownloads(modelParameters);
        if (!cancelled) setMissingNested(missing);
      } catch {
        if (!cancelled) setMissingNested([]);
      }
    };
    const timer = setTimeout(check, 300);
    const unsubscribe = subscribeAnyDownloadState(() => check());
    return () => {
      cancelled = true;
      clearTimeout(timer);
      unsubscribe();
    };
  }, [open, activeStep, JSON.stringify(modelParameters)]);

  useEffect(() => {
    if (
      selectedModel &&
      defaultModelParams &&
      Object.keys(defaultModelParams).length > 0 &&
      !hasLoadedInitialParams
    ) {
      setModelParameters(defaultModelParams);
      setHasLoadedInitialParams(true);
    }
  }, [selectedModel, defaultModelParams, hasLoadedInitialParams]);

  const handleClose = () => {
    setTimeout(() => {
      setActiveStep(0);
      setName("");
      setSelectedModel("");
      setModelParameters({});
      setSelectedOptimizer("");
      setOptimizerParameters({});
      setGoalMetric("");
      setHasUserTouchedName(false);
      setHasLoadedInitialParams(false);
      setUseNestedCV(false);
      setInnerConfig(DEFAULT_INNER_CONFIG);
    }, 100);
    onClose();
  };

  const handleNext = () => {
    if (activeStep === 0) {
      if (!selectedModel) {
        enqueueSnackbar(t("models:error.noModelSelected"), {
          variant: "error",
        });
        handleClose();
        return;
      }

      if (name.trim() === "") {
        enqueueSnackbar(t("models:error.enterModelName"), {
          variant: "warning",
        });
        return;
      }

      const nameExists = existingRuns.some(
        (run) =>
          run.name && run.name.toLowerCase() === name.trim().toLowerCase(),
      );
      if (nameExists) {
        enqueueSnackbar(t("models:error.runNameExists", { name }), {
          variant: "error",
        });
        return;
      }

      if (hasOptimizableParams) {
        setActiveStep(1);
      } else {
        handleCreateRun();
      }
    } else {
      handleCreateRun();
    }
  };

  const handleBack = () => {
    if (activeStep > 0) {
      setActiveStep(activeStep - 1);
      setSelectedOptimizer("");
      setOptimizerParameters({});
      setGoalMetric("");
      setUseNestedCV(false);
      setInnerConfig(DEFAULT_INNER_CONFIG);
    }
  };

  const handleCreateRun = async () => {
    try {
      setLoading(true);

      let nestedConfig = null;
      if (useNestedCV && outerSplit) {
        // Copy the outer splitter configuration and update for inner splitter
        nestedConfig = {
          ...outerSplit,
          splitter_name: innerConfig.splitterType,
          n_splits: innerConfig.nSplits,
        };
      }

      const newRun = await createRun(
        session.id.toString(),
        selectedModel,
        name.trim(),
        modelParameters || {},
        selectedOptimizer || "",
        { ...defaultOptimizerParams, ...optimizerParameters },
        "",
        "",
        "",
        "",
        goalMetric || "",
        "",
        nestedConfig,
      );

      enqueueSnackbar(t("models:message.runCreatedSuccess", { name }), {
        variant: "success",
      });

      let shouldDelayClose = false;
      if (onRunCreated) {
        onRunCreated(newRun);
      }

      if (tourContext?.run && tourContext?.stepIndex === 3) {
        shouldDelayClose = true;
        setTimeout(() => {
          const runCard = document.querySelector(
            '[data-tour="first-run-card"]',
          );
          if (runCard) {
            runCard.scrollIntoView({
              behavior: "smooth",
              block: "center",
              inline: "nearest",
            });
          }
          setTimeout(() => {
            tourContext.nextStep();
            handleClose();
          }, 100);
        }, 100);
      }
      if (!shouldDelayClose) {
        handleClose();
      }
    } catch (error) {
      console.error("Error creating run:", error);

      if (error.response) {
        console.error("Response error:", error.message);
      } else if (error.request) {
        console.error("Request error", error.request);
      } else {
        console.error("Unknown Error", error.message);
      }

      enqueueSnackbar(t("models:error.createRun", { name }), {
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  };

  const handleOptimizerSelected = (optimizerName) => {
    setOptimizerParameters({});
    setSelectedOptimizer(optimizerName);
  };

  // The outer folds are built over the rows left after the carve, so an
  // inner fold cannot draw from the reserved ones.
  const maxInnerFolds = Math.floor(
    (datasetRowCount * (1 - (Number(outerSplit?.test_size) || 0))) /
      outerSplit?.n_splits,
  );

  const isStep1Valid = Boolean(selectedModel && name.trim() !== "");
  const isStep2Valid = Boolean(
    selectedOptimizer &&
    goalMetric &&
    (!useNestedCV ||
      (innerConfig.splitterType &&
        innerConfig.nSplits > 1 &&
        innerConfig.nSplits <= maxInnerFolds)),
  );

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
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
          {t("models:label.addModelToSession")}
          <IconButton
            onClick={handleClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Stepper activeStep={activeStep} sx={{ mb: 6 }}>
          {steps.map((label) => (
            <Step key={label} completed={false}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {activeStep === 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <TextField
              label={t("common:modelName")}
              value={name}
              onChange={(e) => {
                setName(e.target.value);
                setHasUserTouchedName(true);
              }}
              fullWidth
              required
              placeholder={t("common:modelName")}
              helperText={selectedModel ? `Model: ${selectedModel}` : ""}
            />

            {selectedModel && (
              <Box data-tour="model-config">
                <Typography variant="subtitle2" sx={{ mb: 4 }}>
                  {t("common:modelParameters")}
                </Typography>
                <FormSchemaContainer key={selectedModel}>
                  <FormSchemaWithSelectedModel
                    modelToConfigure={selectedModel}
                    initialValues={modelParameters}
                    onFormSubmit={() => {}}
                    onValuesChange={setModelParameters}
                    onCancel={() => {}}
                    hideButtons
                  />
                </FormSchemaContainer>
              </Box>
            )}
          </Box>
        )}

        {activeStep === 1 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 6 }}>
            <Typography variant="subtitle2">
              {t("models:label.optimizerConfiguration")}
            </Typography>

            <Box>
              <Typography variant="body2" sx={{ mb: 2 }}>
                {t("models:label.goalMetric")} *
              </Typography>
              <ModelsTableSelectMetric
                taskName={session?.task_name}
                metricName={goalMetric}
                handleSelectedMetric={setGoalMetric}
                required
                autoSelectDefault
              />
            </Box>

            <Box>
              <Typography variant="body2" sx={{ mb: 1 }}>
                {t("models:label.optimizer")} *
              </Typography>
              <OptimizationTableSelectOptimizer
                taskName={session?.task_name}
                optimizerName={selectedOptimizer}
                handleSelectedOptimizer={handleOptimizerSelected}
                required
              />
            </Box>

            {isCrossValidation && (
              <NestedCVSelector
                useNestedCV={useNestedCV}
                onChange={setUseNestedCV}
                innerConfig={innerConfig}
                onInnerConfigChange={setInnerConfig}
                outerSplit={outerSplit}
                maxInnerFolds={maxInnerFolds}
              />
            )}

            {selectedOptimizer && !optimizerSchemaLoading && (
              <Box sx={{ mt: 4 }}>
                <Typography variant="subtitle2" sx={{ mb: 4 }}>
                  {t("models:label.optimizerParameters")}
                </Typography>
                <FormSchemaContainer key={selectedOptimizer}>
                  <FormSchemaWithSelectedModel
                    modelToConfigure={selectedOptimizer}
                    initialValues={defaultOptimizerParams}
                    onFormSubmit={() => {}}
                    onValuesChange={setOptimizerParameters}
                    onCancel={() => {}}
                    hideButtons
                  />
                </FormSchemaContainer>
              </Box>
            )}
          </Box>
        )}
      </DialogContent>

      <DialogActions sx={{ p: 4, bgcolor: "background.paper" }}>
        <Button variant="outlined" onClick={handleClose} disabled={loading}>
          {t("common:cancel")}
        </Button>
        {activeStep > 0 && (
          <Button variant="outlined" onClick={handleBack} disabled={loading}>
            {t("common:back")}
          </Button>
        )}
        <Tooltip
          title={
            activeStep === 0 && credentialsLocked
              ? t("credentials:requiredTooltip", {
                  platform: requiredPlatforms,
                })
              : activeStep === 0 &&
                  preselectedModelObject?.metadata?.requires_download &&
                  !modelDownloaded
                ? t("common:componentDownload.mustDownload")
                : activeStep === 0 && missingNested.length > 0
                  ? t("common:componentDownload.mustDownloadNested", {
                      names: missingNested
                        .map((m) => m.display_name || m.name)
                        .join(", "),
                    })
                  : ""
          }
        >
          <span>
            <Button
              data-tour="add-model-button"
              onClick={handleNext}
              variant="contained"
              disabled={
                loading ||
                (activeStep === 0 && !isStep1Valid) ||
                (activeStep === 1 && !isStep2Valid) ||
                (activeStep === 0 && credentialsLocked) ||
                (activeStep === 0 &&
                  Boolean(
                    preselectedModelObject?.metadata?.requires_download,
                  ) &&
                  !modelDownloaded) ||
                (activeStep === 0 && missingNested.length > 0)
              }
            >
              {activeStep === steps.length - 1
                ? t("common:addModel")
                : t("common:next")}
            </Button>
          </span>
        </Tooltip>
      </DialogActions>
    </Dialog>
  );
}

AddModelDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  session: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    task_name: PropTypes.string,
    splits: PropTypes.string,
  }),
  preselectedModel: PropTypes.string,
  preselectedModelObject: PropTypes.shape({
    name: PropTypes.string,
    downloaded: PropTypes.bool,
    metadata: PropTypes.object,
  }),
  existingRuns: PropTypes.array,
  onRunCreated: PropTypes.func,
};

export default AddModelDialog;
