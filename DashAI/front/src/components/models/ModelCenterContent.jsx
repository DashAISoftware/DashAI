import { useModels } from "./ModelsContext";
import { useTranslation } from "react-i18next";
import { Box, Typography } from "@mui/material";
import CreateSessionSteps from "./CreateSessionSteps";
import DatasetVisualization from "../DatasetVisualization";
import SelectOptionMenu from "../threeSectionLayout/SelectOptionMenu";
import ModelsBreadcrumbs from "./ModelsBreadcrumbs";
import { useTourContext } from "../tour/TourProvider";
import { useNavigate } from "react-router-dom";
import {
  Category as ClassificationIcon,
  ShowChart as RegressionIcon,
  TextFields as TextClassificationIcon,
  TableChart as TabularClassificationIcon,
  Translate as TranslationIcon,
  ImageSearch as ImageClassificationIcon,
  Science as DefaultTaskIcon,
} from "@mui/icons-material";

const TASK_ICONS = {
  ClassificationTask: ClassificationIcon,
  TabularClassificationTask: TabularClassificationIcon,
  TextClassificationTask: TextClassificationIcon,
  ImageClassificationTask: ImageClassificationIcon,
  RegressionTask: RegressionIcon,
  TranslationTask: TranslationIcon,
};

export default function ModelsCenterContent() {
  const { t } = useTranslation(["models", "datasets", "common"]);
  const tourContext = useTourContext();
  const navigate = useNavigate();
  const {
    sessions,
    setSessions,
    selectedTask,
    tasks,
    loadingTasks,
    datasets,
    selectedDatasetId,
    step,
  } = useModels();

  const goToNextStep = (taskName) => {
    navigate(`/app/models/sessions/new/${taskName}`);

    if (tourContext?.run && tourContext?.stepIndex === 4) {
      const waitForElement = () => {
        const element = document.querySelector(
          '[data-tour="models-dataset-selection"]',
        );
        if (element) {
          tourContext.nextStep();
        } else {
          setTimeout(waitForElement, 100);
        }
      };
      setTimeout(waitForElement, 100);
    }
  };

  const handleBackToTaskSelection = () => {
    navigate("/app/models");
  };

  const handleGoToDatasets = () => {
    navigate("/app/data?action=upload");
  };

  const handleSessionCreated = (newSession) => {
    setSessions((prev) => [...prev, newSession]);
    navigate(`/app/models/sessions/${newSession.id}`);
  };

  const handleNewSessionFromDataset = () => {
    navigate("/app/models", {
      state: { preselectedDatasetId: selectedDatasetId },
    });
  };

  const handleBackToDataset = () => {
    if (selectedDatasetId) {
      navigate(`/app/models/datasets/${selectedDatasetId}`);
      return;
    }
    navigate("/app/models");
  };

  return (
    <>
      {step === 1 && selectedTask ? (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            width: "100%",
            height: "100%",
            overflow: "hidden",
            px: 4,
            pt: 4,
          }}
        >
          <ModelsBreadcrumbs />
          <CreateSessionSteps
            backHome={handleBackToTaskSelection}
            selectedTask={selectedTask}
            datasets={datasets}
            handleSessionCreated={handleSessionCreated}
            existingSessions={sessions}
            preselectedDatasetId={selectedDatasetId}
          />
        </Box>
      ) : step === 2 && selectedDatasetId ? (
        <DatasetVisualization
          dataset={datasets.find((d) => d.id === selectedDatasetId)}
          onItemCreated={handleSessionCreated}
          onNewItem={handleNewSessionFromDataset}
          existingItems={sessions}
          newItemButtonText={t("models:button.createSession")}
        />
      ) : step === 0 ? (
        <SelectOptionMenu
          loading={loadingTasks}
          title={
            selectedDatasetId
              ? t("models:label.selectTaskForSession")
              : t("models:label.modelsModule")
          }
          subtitle={
            selectedDatasetId
              ? t("models:label.chooseTaskForSessionWithDataset", {
                  datasetName: datasets.find((d) => d.id === selectedDatasetId)
                    ?.name,
                })
              : t("models:label.configureTasksTrainCompareModels")
          }
          options={tasks.map((task) => ({
            name: task.name,
            display_name:
              task.display_name ||
              task.name
                .replace("Task", "")
                .replace(/([A-Z])/g, " $1")
                .trim(),
            description:
              task.description || task.metadata?.short_description || "",
            Icon: TASK_ICONS[task.name] || DefaultTaskIcon,
            badge:
              task.metadata?.requires_target === false
                ? t("models:label.unsupervisedBadge")
                : t("models:label.supervisedBadge"),
          }))}
          searchBar={false}
          goToPrevStep={selectedDatasetId ? handleBackToDataset : null}
          showNoDatasetAlert={!selectedDatasetId && datasets.length === 0}
          onGoToDatasets={handleGoToDatasets}
          goToNextStep={goToNextStep}
          dataTour="task-selection"
        />
      ) : null}
    </>
  );
}
