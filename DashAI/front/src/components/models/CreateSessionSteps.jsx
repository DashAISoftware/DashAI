import { useState, useMemo, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, FormControlLabel, Switch, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useFormik } from "formik";
import { useTourContext } from "../tour/TourProvider";
import SetNameAndDatasetStep from "./SetNameAndDatasetStep";
import DatasetSplitStep from "./modelSession/DatasetSplitStep";
import ColumnsStep from "./modelSession/ColumnsStep";
import PreprocessingStep from "./PreprocessingStep";
import DatasetAutocomplete from "../notebooks/notebookCreation/DatasetAutocomplete";
import {
  createModelSession,
  updateModelSession,
  getModelSessionById,
  updateSessionConverters,
} from "../../api/modelSession";
import { getComponents } from "../../api/component";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../utils/nameGenerator";
import { useTranslation } from "react-i18next";
import { useModels } from "./ModelsContext";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";

function CreateSessionSteps({
  backHome,
  selectedTask,
  datasets,
  handleSessionCreated,
  existingSessions = [],
  preselectedDatasetId = null,
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["models", "common"]);
  const tourContext = useTourContext();
  const hasAdvancedTourRef = useRef(false);
  const { setSessionRightContent } = useModels();

  const [selectedDataset, setSelectedDataset] = useState(
    preselectedDatasetId
      ? datasets.find((d) => d.id === preselectedDatasetId) || null
      : null,
  );

  // Holdout or cross-validation
  const [evaluationStrategy, setEvaluationStrategy] = useState(
    "HoldoutEvaluationStrategy",
  );

  const [newExp, setNewExp] = useState({
    name: "",
    dataset: null,
    task_name: selectedTask?.name || "",
    input_columns: [],
    output_columns: [],
    train_metrics: [],
    validation_metrics: [],
    test_metrics: [],
    evaluation_strategy: "",
    splits: {},
    converters: [],
    runs: [],
  });

  // Step 0 (DatasetSplitStep) and step 2 (ColumnsStep) each gate a
  // different footer button ("Siguiente" / "Crear sesión"). They're kept as
  // separate state, rather than one shared flag, because both components
  // stay mounted for the whole wizard lifetime (see the render below) and
  // each keeps re-asserting its own readiness in the background even while
  // hidden on another step — sharing a single flag would let one step's
  // background re-validation silently flip the other step's button.
  const [step0NextEnabled, setStep0NextEnabled] = useState(false);
  // Whether step 0's "Siguiente" advances into the Preprocessing step at
  // all. Off skips straight to Columns — see handleStep0Next and the
  // conditional "Atrás" target on ColumnsStep below. Defaults on so the
  // wizard's existing behavior is unchanged unless the user opts out.
  const [preprocessingEnabled, setPreprocessingEnabled] = useState(true);
  const [columnsNextEnabled, setColumnsNextEnabled] = useState(false);
  const [wizardStep, setWizardStep] = useState(0);
  // Tracks whether the wizard has ever reached step 1, so PreprocessingStep
  // mounts once and then stays mounted (per the "state survives Atrás"
  // rule) — but crucially does NOT mount merely because a dataset is
  // selected while still on step 0. PreprocessingStep pushes its own
  // content into the shared `sessionRightContent` slot unconditionally on
  // mount (unlike DatasetSplitStep, which gates that push on `isActive`),
  // so mounting it early would race DatasetSplitStep for that slot while
  // the user is still configuring the split on step 0.
  const [hasReachedStep1, setHasReachedStep1] = useState(false);
  // Same idea one step further along, for a different (and more damaging)
  // reason: ColumnsStep fetches the session's *current* column set once per
  // refresh signal. Mounting it as soon as the session record exists (i.e.
  // while the user is still on step 0/1) would seed and validate its column
  // picker against the RAW dataset, and it would keep showing that stale set
  // after converters that add/rename/drop columns (PCA, feature selectors,
  // vectorizers) have been applied in step 1 — letting the user finalize a
  // session whose input/output columns don't exist in the preprocessed data.
  const [hasReachedStep2, setHasReachedStep2] = useState(false);

  // Bumped every time step 0's "Siguiente" advances into step 1.
  // PreprocessingStep stays mounted once reached (never remounts on
  // "Atrás"/"Siguiente" toggling, per the note above), so it has no other
  // signal to know it should re-fetch the session — needed so a split
  // change on step 0 that invalidates already-applied converters (see
  // handleStep0Next's `converters_invalidated` branch) is actually
  // reflected here: the stale converter card and stale dataset preview
  // would otherwise linger until some unrelated action forced a refetch.
  const [step1RefreshTrigger, setStep1RefreshTrigger] = useState(0);

  // Same pattern, for step 1 -> step 2: ColumnsStep also stays mounted once
  // reached, so it needs an explicit signal to re-fetch the session's current
  // columns every time the user comes forward from the preprocessing step —
  // otherwise the column picker keeps offering (and validating against) the
  // column set as it was the first time step 2 was opened, ignoring every
  // converter applied afterwards.
  const [step2RefreshTrigger, setStep2RefreshTrigger] = useState(0);

  // null until step 0's "Siguiente" successfully creates the session record;
  // from then on, returning to step 0 and moving forward again PATCHes the
  // existing session instead of creating a second one.
  const [modelSessionId, setModelSessionId] = useState(null);
  const [isAdvancingStep0, setIsAdvancingStep0] = useState(false);
  const [isFinalizing, setIsFinalizing] = useState(false);

  // Captures the PATCH closure ColumnsStep hands up via `onReadyToFinalize`,
  // re-supplied every time the user's column selection changes so the
  // wizard's "Crear sesión" button always closes over the latest choice.
  const finalizeColumnsRef = useRef(null);
  const handleColumnsReadyToFinalize = (finalizeFn) => {
    finalizeColumnsRef.current = finalizeFn;
  };

  const handleDatasetChange = (newDataset) => {
    setSelectedDataset(newDataset);
    setStep0NextEnabled(false);
    // The dataset picker lives on step 0, which stays reachable via "Atrás"
    // after the session record already exists. A session is permanently bound
    // to the dataset it was created with (its converters and preprocessed
    // partitions are derived from it), and step 0's PATCH branch only sends
    // splits/evaluation_strategy — so silently keeping the old session here
    // would leave it pointing at the previous dataset while every later step
    // works against the new one. Dropping the id instead makes step 0's
    // "Siguiente" create a fresh session for the new dataset, which is both
    // simpler and safer than trying to re-point an existing one.
    setModelSessionId(null);
    setHasReachedStep1(false);
    setHasReachedStep2(false);
    setColumnsNextEnabled(false);
    setPreprocessingEnabled(true);
    // Drops the finalize closure ColumnsStep handed up, which captured the
    // now-abandoned session id.
    finalizeColumnsRef.current = null;
    setNewExp((prev) => ({
      ...prev,
      dataset: newDataset,
      input_columns: [],
      output_columns: [],
      splits: {},
      converters: [],
    }));
    if (
      tourContext?.run &&
      tourContext?.stepIndex === 5 &&
      newDataset &&
      !hasAdvancedTourRef.current
    ) {
      hasAdvancedTourRef.current = true;
      const waitForElement = () => {
        const element = document.querySelector(
          '[data-tour="models-validation-alert"]',
        );
        if (element) {
          tourContext.nextStep();
        } else {
          setTimeout(waitForElement, 100);
        }
      };
      setTimeout(waitForElement, 200);
    }
  };

  const { defaultName } = useMemo(() => {
    if (!selectedTask) {
      return { defaultName: "" };
    }

    const taskDisplayName =
      selectedTask.metadata?.display_name ||
      selectedTask.name
        .replace("Task", "")
        .replace(/([A-Z])/g, " $1")
        .trim();

    return generateSequentialName({
      base: `Session_${taskDisplayName}`,
      items: existingSessions,
      filter: (session) => session.task_name === selectedTask.name,
    });
  }, [selectedTask, existingSessions]);

  const formik = useFormik({
    initialValues: {
      name: "",
    },
    enableReinitialize: true,
    onSubmit: () => {},
  });

  useEffect(() => {
    if (selectedTask && defaultName && !formik.values.name.trim()) {
      formik.setFieldValue("name", defaultName);
    }
  }, [selectedTask, defaultName, formik]);

  useEffect(() => {
    if (selectedDataset) return;
    setSessionRightContent(
      <Box
        sx={{
          display: "flex",
          height: "100%",
          justifyContent: "center",
          alignItems: "center",
          p: 4,
        }}
      >
        <Typography variant="body2" color="text.secondary" textAlign="center">
          {t("models:label.selectDatasetFirst")}
        </Typography>
      </Box>,
    );
    return () => setSessionRightContent(null);
  }, [selectedDataset]);

  const isStep0NextEnabled =
    formik.values.name.trim().length >= 4 &&
    selectedDataset !== null &&
    step0NextEnabled;

  // Turning preprocessing off while the session already has converters
  // applied would otherwise leave them silently in effect — the toggle
  // would say "no preprocessing" while the session still had some. Clears
  // them the same way a split change already invalidates them, so "off"
  // always means what it says.
  const handlePreprocessingToggle = async (checked) => {
    setPreprocessingEnabled(checked);
    if (checked || modelSessionId == null) return;
    try {
      const session = await getModelSessionById(modelSessionId);
      if (session.converters && session.converters.length > 0) {
        await updateSessionConverters(modelSessionId, []);
        enqueueSnackbar(
          t("models:message.convertersRemovedByPreprocessingToggle"),
          { variant: "warning" },
        );
      }
    } catch (error) {
      console.error(
        "Error clearing converters after disabling preprocessing:",
        error,
      );
    }
  };

  const isCrossValidation =
    evaluationStrategy === "CrossValidationEvaluationStrategy";

  // Preprocessing + cross-validation isn't supported yet (see this
  // session's design discussion) — force the toggle off, clearing any
  // already-applied converters the same way a manual toggle-off does, the
  // moment the user switches to cross-validation.
  useEffect(() => {
    if (isCrossValidation && preprocessingEnabled) {
      handlePreprocessingToggle(false);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [isCrossValidation]);

  // Shared tail for both handleStep0Next branches: advance into
  // Preprocessing normally, or skip straight to Columns when the toggle is
  // off — mirrors handleStep1Next's own step2RefreshTrigger/
  // columnsNextEnabled reset, since ColumnsStep must (re-)read the
  // session's current (here: still raw, no converters) column set either
  // way.
  const advanceFromStep0 = () => {
    if (preprocessingEnabled) {
      setHasReachedStep1(true);
      setStep1RefreshTrigger((n) => n + 1);
      setWizardStep(1);
    } else {
      setHasReachedStep2(true);
      setStep2RefreshTrigger((n) => n + 1);
      setColumnsNextEnabled(false);
      setWizardStep(2);
    }
  };

  // End of step 0: create the session on first advance, or PATCH the
  // existing one (split/strategy only) when the user came back from a later
  // step and is moving forward again.
  const handleStep0Next = async () => {
    setIsAdvancingStep0(true);
    try {
      if (modelSessionId == null) {
        let allMetricNames = [];
        try {
          const metricsData = await getComponents({
            selectTypes: ["Metric"],
            relatedComponent: newExp.task_name,
          });
          allMetricNames = metricsData.map((metric) => metric.name);
        } catch (error) {
          console.warn("Could not fetch metrics:", error);
        }

        const hasTrain =
          (newExp.splits.train !== undefined && newExp.splits.train !== 0) ||
          evaluationStrategy === "CrossValidationEvaluationStrategy";
        const hasValidation =
          newExp.splits.validation !== undefined &&
          newExp.splits.validation !== 0;
        const hasTest =
          (newExp.splits.test !== undefined && newExp.splits.test !== 0) ||
          evaluationStrategy === "CrossValidationEvaluationStrategy";

        let effectiveName = formik.values.name.trim();
        let response;
        try {
          response = await createModelSession(
            selectedDataset.id,
            selectedTask?.name || newExp.task_name,
            effectiveName,
            [],
            [],
            hasTrain ? allMetricNames : [],
            hasValidation ? allMetricNames : [],
            hasTest ? allMetricNames : [],
            newExp.evaluation_strategy,
            JSON.stringify(newExp.splits),
            [],
          );
        } catch (createError) {
          if (createError?.response?.status === 409) {
            effectiveName = getNextAvailableName(
              effectiveName,
              existingSessions,
            );
            formik.setFieldValue("name", effectiveName);
            response = await createModelSession(
              selectedDataset.id,
              selectedTask?.name || newExp.task_name,
              effectiveName,
              [],
              [],
              hasTrain ? allMetricNames : [],
              hasValidation ? allMetricNames : [],
              hasTest ? allMetricNames : [],
              newExp.evaluation_strategy,
              JSON.stringify(newExp.splits),
              [],
            );
          } else {
            throw createError;
          }
        }

        setModelSessionId(response.id);
        enqueueSnackbar(t("models:message.sessionCreatedSuccess"), {
          variant: "success",
        });
        advanceFromStep0();
      } else {
        const updated = await updateModelSession({
          id: modelSessionId,
          formData: {
            splits: JSON.stringify(newExp.splits),
            evaluation_strategy: newExp.evaluation_strategy,
          },
        });

        if (updated?.converters_invalidated) {
          enqueueSnackbar(
            t("models:message.convertersInvalidatedBySplitChange"),
            { variant: "warning" },
          );
        }
        advanceFromStep0();
      }
    } catch (error) {
      enqueueSnackbar(t("models:error.createSession"), {
        variant: "error",
      });
      console.error("Error creating/updating session:", error);
    } finally {
      setIsAdvancingStep0(false);
    }
  };

  // End of step 1: no session mutation is needed (converters are already
  // persisted as they're applied), but step 2 must (re-)read the session's
  // current column set every time it's entered — see step2RefreshTrigger.
  const handleStep1Next = () => {
    setHasReachedStep2(true);
    setStep2RefreshTrigger((n) => n + 1);
    // Re-review gap (a): without this, a return visit to step 2 keeps
    // "Crear sesión" enabled with the pre-refresh selection for the
    // duration of the columns refetch + validation below, letting a
    // double-click finalize a stale selection.
    setColumnsNextEnabled(false);
    setWizardStep(2);
  };

  // End of step 2: PATCH the final input/output columns via the closure
  // ColumnsStep supplied, then navigate to the created session's detail
  // view — the same navigation `handleSessionCreated` already performed
  // after the old flow's atomic POST, just fired here instead.
  const handleFinalize = async () => {
    if (!finalizeColumnsRef.current) return;
    setIsFinalizing(true);
    try {
      const response = await finalizeColumnsRef.current();

      if (tourContext?.run) {
        tourContext.stopTour();
        sessionStorage.setItem("startModelsSessionTour", "true");
      }

      if (handleSessionCreated) {
        handleSessionCreated(response);
      }
    } catch (error) {
      enqueueSnackbar(t("models:error.createSession"), {
        variant: "error",
      });
      console.error("Error finalizing session:", error);
    } finally {
      setIsFinalizing(false);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      {/* All three steps stay mounted (hidden via CSS) instead of
          unmounting as the wizard advances — DatasetSplitStep,
          PreprocessingStep and ColumnsStep each hold local-only state
          (split type/shuffle/seed/CV config, drag state, column
          selection...) that resets to defaults on every fresh mount, so a
          real unmount here would silently drop anything the user
          customized the moment they went "Atrás". */}
      <Box
        sx={{
          display: wizardStep === 0 ? "flex" : "none",
          flexDirection: "column",
          height: "100%",
          minHeight: 0,
        }}
      >
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" component="h1">
            {t("models:label.prepareDataset")}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t("models:label.selectDatasetAndPrepare")}
          </Typography>
        </Box>

        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            pt: 2,
            display: "flex",
            flexDirection: "column",
            gap: 4,
          }}
        >
          <SetNameAndDatasetStep formik={formik} />
          <DatasetAutocomplete
            datasets={datasets}
            selectedDataset={selectedDataset}
            setSelectedDataset={handleDatasetChange}
          />
          {selectedDataset && (
            <DatasetSplitStep
              key={selectedDataset.id}
              newExp={newExp}
              setNewExp={setNewExp}
              setNextEnabled={setStep0NextEnabled}
              evaluationStrategy={evaluationStrategy}
              setEvaluationStrategy={setEvaluationStrategy}
              dataset={selectedDataset}
              isActive={wizardStep === 0}
            />
          )}
          {selectedDataset && (
            <Box
              sx={{
                mt: 2,
                p: 6,
                border: 1,
                borderColor: "divider",
                borderRadius: 2,
              }}
            >
              <FormControlLabel
                control={
                  <Switch
                    checked={preprocessingEnabled}
                    disabled={isCrossValidation}
                    onChange={(e) =>
                      handlePreprocessingToggle(e.target.checked)
                    }
                  />
                }
                label={t("models:label.enablePreprocessing")}
              />
              <Typography variant="body2" color="text.secondary">
                {isCrossValidation
                  ? t("models:label.enablePreprocessingUnavailableWithCV")
                  : preprocessingEnabled
                    ? t("models:label.enablePreprocessingDescriptionOn")
                    : t("models:label.enablePreprocessingDescriptionOff")}
              </Typography>
            </Box>
          )}
        </Box>

        <StepperNavigationFooter
          onBack={backHome}
          onNext={handleStep0Next}
          nextDisabled={!isStep0NextEnabled}
          loading={isAdvancingStep0}
          nextDataTour={tourContext?.run ? "models-next-button" : undefined}
        />
      </Box>

      <Box
        sx={{
          display: wizardStep === 1 ? "flex" : "none",
          flexDirection: "column",
          height: "100%",
          minHeight: 0,
        }}
      >
        {selectedDataset && hasReachedStep1 && (
          <PreprocessingStep
            newExp={newExp}
            setNewExp={setNewExp}
            dataset={selectedDataset}
            modelSessionId={modelSessionId}
            refreshTrigger={step1RefreshTrigger}
            isActive={wizardStep === 1}
            onBack={() => setWizardStep(0)}
            onCreateSession={handleStep1Next}
          />
        )}
      </Box>

      <Box
        sx={{
          display: wizardStep === 2 ? "flex" : "none",
          flexDirection: "column",
          height: "100%",
          minHeight: 0,
        }}
      >
        <Box sx={{ mb: 4 }}>
          <Typography variant="h5" component="h1">
            {t("models:label.selectColumns")}
          </Typography>
          <Typography variant="body2" color="text.secondary">
            {t("models:label.selectColumnsDescription")}
          </Typography>
        </Box>

        <Box
          sx={{
            flex: 1,
            minHeight: 0,
            overflowY: "auto",
            pt: 2,
          }}
        >
          {selectedDataset && hasReachedStep2 && modelSessionId != null && (
            <ColumnsStep
              modelSessionId={modelSessionId}
              taskName={newExp.task_name}
              dataset={selectedDataset}
              refreshTrigger={step2RefreshTrigger}
              setNextEnabled={setColumnsNextEnabled}
              onReadyToFinalize={handleColumnsReadyToFinalize}
            />
          )}
        </Box>

        <StepperNavigationFooter
          onBack={() => setWizardStep(preprocessingEnabled ? 1 : 0)}
          onNext={handleFinalize}
          nextDisabled={!columnsNextEnabled}
          nextLabel={t("models:button.createSession")}
          loading={isFinalizing}
        />
      </Box>
    </Box>
  );
}

CreateSessionSteps.propTypes = {
  backHome: PropTypes.func.isRequired,
  selectedTask: PropTypes.object.isRequired,
  datasets: PropTypes.array.isRequired,
  handleSessionCreated: PropTypes.func,
  existingSessions: PropTypes.array,
  preselectedDatasetId: PropTypes.number,
};

export default CreateSessionSteps;
