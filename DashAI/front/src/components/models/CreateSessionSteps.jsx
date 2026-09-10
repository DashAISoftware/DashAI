import { useState, useMemo, useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useFormik } from "formik";
import { useTourContext } from "../tour/TourProvider";
import SetNameAndDatasetStep from "./SetNameAndDatasetStep";
import PrepareDatasetStep from "./modelSession/PrepareDatasetStep";
import DatasetAutocomplete from "../notebooks/notebookCreation/DatasetAutocomplete";
import { createModelSession } from "../../api/modelSession";
import { getComponents } from "../../api/component";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../utils/nameGenerator";
import { useTranslation } from "react-i18next";
import { useModels } from "./ModelsContext";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";
import { hasPartition } from "../../utils/splitsPayload";

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
  });

  const [nextEnabled, setNextEnabled] = useState(false);

  const handleDatasetChange = (newDataset) => {
    setSelectedDataset(newDataset);
    setNextEnabled(false);
    setNewExp((prev) => ({
      ...prev,
      dataset: newDataset,
      input_columns: [],
      output_columns: [],
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

  const isNextEnabled =
    formik.values.name.trim().length >= 4 &&
    selectedDataset !== null &&
    nextEnabled;

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
          );
        } else {
          throw createError;
        }
      }

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
          <PrepareDatasetStep
            key={selectedDataset.id}
            newExp={newExp}
            setNewExp={setNewExp}
            setNextEnabled={setNextEnabled}
            evaluationStrategy={evaluationStrategy}
            setEvaluationStrategy={setEvaluationStrategy}
            dataset={selectedDataset}
          />
        )}
      </Box>

      <StepperNavigationFooter
        onBack={backHome}
        onNext={formik.handleSubmit}
        nextDisabled={!isNextEnabled}
        nextLabel={t("models:button.createSession")}
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
