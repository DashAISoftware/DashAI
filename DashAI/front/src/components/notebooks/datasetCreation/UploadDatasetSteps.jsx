import { useState, useRef, useEffect } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import SelectDataloaderStep from "./SelectDataloaderStep";
import ConfigureAndUploadDatasetStep from "./ConfigureAndUploadDatasetStep";
import DataloaderConfigBar from "./DataloaderConfigBar";
import { Box, Typography } from "@mui/material";
import ComponentDetailsPanel from "../../custom/ComponentDetailsPanel";
import { useTranslation } from "react-i18next";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { useTourContext } from "../../tour/TourProvider";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { useSnackbar } from "notistack";

const UPLOAD_BASE_PATH = "/app/data/datasets/new";

export default function UploadDatasetSteps({ backHome }) {
  const {
    datasets,
    addDatasetOptimistically,
    startDatasetPolling,
    setRightBarContent,
    setUploadDataloader,
  } = useDatasetsAndNotebooks();

  const navigate = useNavigate();
  const { dataloaderName } = useParams();
  const step = dataloaderName ? 1 : 0;

  const [selectedDataloader, setSelectedDataloader] = useState();
  const [dataloaders, setDataloaders] = useState([]);
  const [loadingDataloaders, setLoadingDataloaders] = useState(true);
  const [formValues, setFormValues] = useState({});
  const [error, setError] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [computeMetadata, setComputeMetadata] = useState(true);

  const handleComputeMetadataChange = (next) => {
    setComputeMetadata(next);
  };
  const { t } = useTranslation(["datasets"]);
  const { enqueueSnackbar } = useSnackbar();
  const tourContext = useTourContext();

  const formSubmitRef = useRef(null);

  useEffect(() => {
    async function fetchDataloaders() {
      setLoadingDataloaders(true);
      try {
        const list = await getComponentsRequest({
          selectTypes: ["DataLoader"],
        });
        setDataloaders(list);
      } catch (error) {
        enqueueSnackbar(t("datasets:error.fetchingDataloaders"), {
          variant: "error",
        });
      } finally {
        setLoadingDataloaders(false);
      }
    }
    fetchDataloaders();
  }, [t]);

  // Sync selected dataloader from URL param, or redirect if unknown
  useEffect(() => {
    if (!dataloaderName || loadingDataloaders || dataloaders.length === 0)
      return;
    const match = dataloaders.find((d) => d.name === dataloaderName);
    if (match) {
      setSelectedDataloader(match);
    } else {
      navigate(UPLOAD_BASE_PATH, { replace: true });
    }
  }, [dataloaderName, loadingDataloaders, dataloaders, navigate]);

  const goToNextStep = () => {
    navigate(`${UPLOAD_BASE_PATH}/${selectedDataloader.name}`);
  };

  const goToPrevStep = () => {
    if (step === 0) {
      backHome();
      return;
    }
    navigate(UPLOAD_BASE_PATH);
  };

  const getTitle = () => {
    switch (step) {
      case 0:
        return t("datasets:label.selectDataloader");
      case 1:
        return t("datasets:label.uploadDataset");
      default:
        return t("datasets:label.createDataset");
    }
  };

  const getSubtitle = () => {
    switch (step) {
      case 0:
        return t("datasets:label.selectUploadMethod");
      case 1:
        return t("datasets:label.uploadAndConfigure");
      default:
        return t("datasets:label.configureDataset");
    }
  };

  // Sync selected dataloader to context so DataBreadcrumbs can show display_name
  useEffect(() => {
    if (setUploadDataloader) {
      setUploadDataloader(selectedDataloader?.name ? selectedDataloader : null);
    }
  }, [selectedDataloader, setUploadDataloader]);

  // Clear right sidebar and dataloader on unmount
  useEffect(() => {
    return () => {
      if (setRightBarContent) setRightBarContent(null);
      if (setUploadDataloader) setUploadDataloader(null);
    };
  }, [setRightBarContent, setUploadDataloader]);

  // Update the right sidebar based on current step
  useEffect(() => {
    if (!setRightBarContent) return;

    if (step === 0) {
      setRightBarContent(
        <ComponentDetailsPanel component={selectedDataloader} />,
      );
    } else if (step === 1 && selectedDataloader?.name) {
      setRightBarContent(
        <DataloaderConfigBar
          selectedDataloader={selectedDataloader.name}
          formSubmitRef={formSubmitRef}
          setError={setError}
          onValuesChange={setFormValues}
          computeMetadata={computeMetadata}
          onComputeMetadataChange={handleComputeMetadataChange}
        />,
      );
    } else {
      setRightBarContent(null);
    }
  }, [step, selectedDataloader, datasets, setRightBarContent, computeMetadata]);

  const handleDatasetCreated = (newDataset, datasetJob) => {
    addDatasetOptimistically(newDataset);
    setRightBarContent(null);
    startDatasetPolling(newDataset, datasetJob);
    navigate(`/app/data/datasets/${newDataset.id}`);

    if (tourContext?.run) {
      tourContext.stopTour();
      sessionStorage.setItem("startDatasetViewTour", "true");
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
          {getTitle()}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {getSubtitle()}
        </Typography>
      </Box>

      {step === 0 && (
        <SelectDataloaderStep
          goToNextStep={goToNextStep}
          goToPrevStep={goToPrevStep}
          selectedDataloader={selectedDataloader}
          setSelectedDataloader={setSelectedDataloader}
          dataloaders={dataloaders}
          loadingDataloaders={loadingDataloaders}
        />
      )}
      {step === 1 && selectedDataloader?.name && (
        <ConfigureAndUploadDatasetStep
          goToPrevStep={goToPrevStep}
          selectedDataloader={selectedDataloader}
          backHome={backHome}
          handleDatasetCreated={handleDatasetCreated}
          formSubmitRef={formSubmitRef}
          formValues={formValues}
          onPreviewError={setPreviewError}
          formHasErrors={error}
          existingDatasets={datasets}
          computeMetadata={computeMetadata}
        />
      )}
    </Box>
  );
}
