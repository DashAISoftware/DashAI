import { useState, useMemo, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Typography, CircularProgress } from "@mui/material";
import { useSnackbar } from "notistack";
import { useFormik } from "formik";
import { useTourContext } from "../tour/TourProvider";
import SetNameAndDatasetStep from "./SetNameAndDatasetStep";
import PrepareDatasetStep from "./modelSession/PrepareDatasetStep";
import PreprocessingStep from "./modelSession/PreprocessingStep";
import SelectColumnsStep from "./modelSession/SelectColumnsStep";
import DatasetAutocomplete from "../notebooks/notebookCreation/DatasetAutocomplete";
import { createModelSession } from "../../api/modelSession";
import { forceRefreshNow } from "../../utils/jobPoller";
import { getComponents } from "../../api/component";
import {
  getDatasetInfo as getDatasetInfoRequest,
  getDatasetTypes as getDatasetTypesRequest,
} from "../../api/datasets";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../utils/nameGenerator";
import { useTranslation } from "react-i18next";
import { useModels } from "./ModelsContext";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";
import { hasPartition } from "../../utils/splitsPayload";

const STEP_PREPARE_DATASET = "prepareDataset";
const STEP_PREPROCESSING = "preprocessing";
const STEP_SELECT_COLUMNS = "selectColumns";

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

  // Which evaluation strategy the session uses. Left empty until the task's
  // strategies load, since which ones exist depends on the task.
  const [evaluationStrategy, setEvaluationStrategy] = useState(null);

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
    runs: [],
    applyPreprocessing: false,
    preprocessing: [],
    input_column_refs: [],
  });

  const [nextEnabled, setNextEnabled] = useState(false);
  const [currentStep, setCurrentStep] = useState(STEP_PREPARE_DATASET);

  const [datasetInfo, setDatasetInfo] = useState({});
  const [datasetTypes, setDatasetTypes] = useState({});
  const [infoLoading, setInfoLoading] = useState(false);

  useEffect(() => {
    if (!selectedDataset?.id) {
      setDatasetInfo({});
      setDatasetTypes({});
      return;
    }
    let cancelled = false;
    setInfoLoading(true);
    (async () => {
      try {
        const [fetchedInfo, fetchedTypes] = await Promise.all([
          getDatasetInfoRequest(selectedDataset.id),
          getDatasetTypesRequest(selectedDataset.id),
        ]);
        if (cancelled) return;
        setDatasetInfo(fetchedInfo);
        setDatasetTypes(fetchedTypes);
      } catch (error) {
        if (!cancelled) {
          enqueueSnackbar(t("experiments:error.errorFetchingDatasetInfo"));
          console.error("Error fetching dataset info:", error);
        }
      } finally {
        if (!cancelled) setInfoLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedDataset?.id]);

  const steps = useMemo(
    () => [
      STEP_PREPARE_DATASET,
      ...(newExp.applyPreprocessing ? [STEP_PREPROCESSING] : []),
      STEP_SELECT_COLUMNS,
    ],
    [newExp.applyPreprocessing],
  );
  const currentStepIndex = Math.max(0, steps.indexOf(currentStep));
  const isFirstStep = currentStepIndex === 0;
  const isLastStep = currentStepIndex === steps.length - 1;

  const handleDatasetChange = (newDataset) => {
    setSelectedDataset(newDataset);
    setNextEnabled(false);
    setNewExp((prev) => ({
      ...prev,
      dataset: newDataset,
      input_columns: [],
      output_columns: [],
      input_column_refs: [],
      splits: {},
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
    onSubmit: async (values) => {
      await createSession(values.name.trim());
    },
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

  const isNextEnabled = isFirstStep
    ? formik.values.name.trim().length >= 4 &&
      selectedDataset !== null &&
      nextEnabled
    : nextEnabled;

  const goToStep = (step) => {
    setNextEnabled(false);
    setCurrentStep(step);
  };

  const handleFooterBack = () => {
    if (isFirstStep) {
      backHome();
      return;
    }
    goToStep(steps[currentStepIndex - 1]);
  };

  const handleFooterNext = () => {
    if (isLastStep) {
      formik.handleSubmit();
      return;
    }
    goToStep(steps[currentStepIndex + 1]);
  };

  const createSession = async (sessionName) => {
    try {
      setNextEnabled(false);

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

      const hasTrain = hasPartition(newExp.splits, "train");
      const hasValidation = hasPartition(newExp.splits, "validation");
      const hasTest = hasPartition(newExp.splits, "test");

      let effectiveName = sessionName;
      let response;
      try {
        response = await createModelSession(
          selectedDataset.id,
          selectedTask?.name || newExp.task_name,
          effectiveName,
          newExp.input_columns,
          newExp.output_columns,
          hasTrain ? allMetricNames : [],
          hasValidation ? allMetricNames : [],
          hasTest ? allMetricNames : [],
          newExp.evaluation_strategy,
          JSON.stringify(newExp.splits),
          newExp.preprocessing,
          newExp.input_column_refs,
        );
      } catch (createError) {
        if (createError?.response?.status === 409) {
          effectiveName = getNextAvailableName(effectiveName, existingSessions);
          formik.setFieldValue("name", effectiveName);
          response = await createModelSession(
            selectedDataset.id,
            selectedTask?.name || newExp.task_name,
            effectiveName,
            newExp.input_columns,
            newExp.output_columns,
            hasTrain ? allMetricNames : [],
            hasValidation ? allMetricNames : [],
            hasTest ? allMetricNames : [],
            newExp.evaluation_strategy,
            JSON.stringify(newExp.splits),
            newExp.preprocessing,
            newExp.input_column_refs,
          );
        } else {
          throw createError;
        }
      }

      // The session's PreprocessingJob (if any) is already enqueued by the
      // time this response comes back — force an immediate poll so the job
      // queue widget picks it up right away instead of waiting for its next
      // 1s tick, which the job can easily finish before (see
      // ConfigureAndUploadDatasetStep.jsx for the same pattern).
      forceRefreshNow();

      enqueueSnackbar(t("models:message.sessionCreatedSuccess"), {
        variant: "success",
      });

      formik.resetForm();

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
      console.error("Error creating session:", error);
    }
  };

  const stepTitle = {
    [STEP_PREPARE_DATASET]: t("models:label.prepareDataset"),
    [STEP_PREPROCESSING]: t("models:label.preprocessingOptional"),
    [STEP_SELECT_COLUMNS]: t("models:label.selectColumnsTitle"),
  }[currentStep];

  const stepSubtitle = {
    [STEP_PREPARE_DATASET]: t("models:label.selectDatasetAndPrepare"),
    [STEP_PREPROCESSING]: t("models:label.preprocessingOptionalDescription"),
    [STEP_SELECT_COLUMNS]: t("models:label.selectColumnsDescription"),
  }[currentStep];

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1">
          {stepTitle}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {stepSubtitle}
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
        {currentStep === STEP_PREPARE_DATASET && (
          <>
            <SetNameAndDatasetStep formik={formik} />
            <DatasetAutocomplete
              datasets={datasets}
              selectedDataset={selectedDataset}
              setSelectedDataset={handleDatasetChange}
            />
            {selectedDataset && (
              <PrepareDatasetStep
                key={selectedDataset.id}
                newExp={newExp}
                setNewExp={setNewExp}
                setNextEnabled={setNextEnabled}
                evaluationStrategy={evaluationStrategy}
                setEvaluationStrategy={setEvaluationStrategy}
                dataset={selectedDataset}
                datasetInfo={datasetInfo}
                infoLoading={infoLoading}
              />
            )}
          </>
        )}

        {currentStep === STEP_PREPROCESSING && selectedDataset && (
          <PreprocessingStep
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
            dataset={selectedDataset}
            datasetTypes={datasetTypes}
          />
        )}

        {currentStep === STEP_SELECT_COLUMNS && selectedDataset && (
          <>
            {infoLoading ? (
              <Box sx={{ display: "flex", justifyContent: "center" }}>
                <CircularProgress />
              </Box>
            ) : (
              <SelectColumnsStep
                newExp={newExp}
                setNewExp={setNewExp}
                setNextEnabled={setNextEnabled}
                dataset={selectedDataset}
                datasetInfo={datasetInfo}
                datasetTypes={datasetTypes}
              />
            )}
          </>
        )}
      </Box>

      <StepperNavigationFooter
        onBack={handleFooterBack}
        onNext={handleFooterNext}
        nextDisabled={!isNextEnabled}
        nextLabel={
          isLastStep ? t("models:button.createSession") : t("common:next")
        }
        nextDataTour={tourContext?.run ? "models-next-button" : undefined}
      />
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
