import { useCallback, useEffect } from "react";
import { useLocation, useNavigate, useSearchParams } from "react-router-dom";
import { Box } from "@mui/material";
import NotebookVisualization from "../notebook/NotebookVisualization";
import UploadDatasetSteps from "../datasetCreation/UploadDatasetSteps";
import UploadNotebookSteps from "../notebookCreation/UploadNotebookSteps";
import DatasetVisualization from "../../DatasetVisualization";
import SelectOptionMenu from "../../threeSectionLayout/SelectOptionMenu";
import DataBreadcrumbs from "../DataBreadcrumbs";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";
import {
  CloudUpload as UploadDatasetIcon,
  AutoStories as NotebookIcon,
  Hub as HubIcon,
} from "@mui/icons-material";

export default function DatasetsCenterContent() {
  const {
    datasets,
    notebooks,
    selectedDatasetId,
    selectedNotebookId,
    setRightBarContent,
    step,
    addNotebookOptimistically,
    selectedOption,
  } = useDatasetsAndNotebooks();

  const tourContext = useTourContext();
  const { t } = useTranslation(["datasets", "common"]);
  const navigate = useNavigate();
  const location = useLocation();
  const [searchParams, setSearchParams] = useSearchParams();
  const preselectedDatasetIdFromState =
    location.state?.preselectedDatasetId ?? null;

  useEffect(() => {
    if (searchParams.get("action") === "upload") {
      searchParams.delete("action");
      setSearchParams(searchParams, { replace: true });
      navigate("/app/data/datasets/new");
    }
  }, [searchParams]);

  const selectedDataset = datasets.find((n) => n.id === selectedDatasetId);
  const selectedNotebook = notebooks.find((n) => n.id === selectedNotebookId);

  const goToNextStep = useCallback(
    (option) => {
      if (option === "dataset") {
        navigate("/app/data/datasets/new");
        if (tourContext?.run) {
          setTimeout(() => {
            tourContext.nextStep();
          }, 600);
        }
        return;
      }

      if (option === "hub") {
        navigate("/app/data/hub");
        return;
      }

      navigate("/app/data/notebooks/new");
    },
    [tourContext, navigate],
  );

  const handleNotebookCreated = (createdNotebook) => {
    addNotebookOptimistically(createdNotebook);
    navigate(`/app/data/notebooks/${createdNotebook.id}`);
  };

  const handleNewNotebookFromDataset = () => {
    navigate("/app/data/notebooks/new", {
      state: { preselectedDatasetId: selectedDatasetId },
    });
  };

  if (selectedNotebookId && selectedOption === "notebook") {
    return (
      <NotebookVisualization
        key={selectedNotebookId}
        notebook={selectedNotebook}
        existingDatasets={datasets}
      />
    );
  }

  if (selectedDatasetId && selectedOption === "dataset") {
    return (
      <DatasetVisualization
        dataset={selectedDataset}
        onNewItem={handleNewNotebookFromDataset}
        newItemButtonText={t("datasets:button.newNotebook")}
        tourContextType="datasets"
      />
    );
  }

  if (step === 1 && selectedOption === "dataset") {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          overflow: "auto",
          px: 4,
          pt: 4,
        }}
      >
        <DataBreadcrumbs />
        <UploadDatasetSteps
          backHome={() => {
            setRightBarContent(null);
            navigate("/app/data");
          }}
        />
      </Box>
    );
  }
  if (step === 1 && selectedOption === "notebook") {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          width: "100%",
          height: "100%",
          overflow: "auto",
          px: 4,
          pt: 4,
        }}
      >
        <DataBreadcrumbs />
        <UploadNotebookSteps
          backHome={() => {
            navigate("/app/data");
          }}
          datasets={datasets}
          handleNotebookCreated={handleNotebookCreated}
          existingNotebooks={notebooks}
          preselectedDatasetId={preselectedDatasetIdFromState}
        />
      </Box>
    );
  }
  if (step === 0) {
    return (
      <SelectOptionMenu
        title={t("datasets:label.datasetModule")}
        subtitle={t("datasets:label.datasetModuleSubtitle")}
        options={[
          {
            name: "dataset",
            display_name: t("datasets:label.uploadDataset"),
            description: t("datasets:label.uploadDatasetDescription"),
            Icon: UploadDatasetIcon,
            "data-tour": "dataset-option",
          },
          {
            name: "notebook",
            display_name: t("datasets:label.createNewNotebook"),
            description: t("datasets:label.createNewNotebookDescription"),
            Icon: NotebookIcon,
            "data-tour": "notebook-option",
          },
        ]}
        searchBar={false}
        goToNextStep={goToNextStep}
      />
    );
  }
  return null;
}
