import { useState, useRef, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import SelectDataloaderStep from "../datasetCreation/SelectDataloaderStep";
import ConfigureAndUploadDatasetStep from "../datasetCreation/ConfigureAndUploadDatasetStep";
import DataloaderConfigBar from "../datasetCreation/DataloaderConfigBar";
import ConfigureAndUploadDocumentStep from "../documentCreation/ConfigureAndUploadDocumentStep";
import DocumentLoaderConfigBar from "../documentCreation/DocumentLoaderConfigBar";
import ComponentDetailsPanel from "../../custom/ComponentDetailsPanel";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { useTourContext } from "../../tour/TourProvider";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { loadsDataKind } from "../../../utils/dataKinds";

const UPLOAD_BASE_PATH = "/app/data/new";

function loaderDataKind(loader) {
  return loadsDataKind(loader, "document") ? "document" : "dataset";
}

export default function UploadDataSteps({ backHome }) {
  const {
    datasets,
    documents,
    addDatasetOptimistically,
    startDatasetPolling,
    addDocumentOptimistically,
    startDocumentPolling,
    setRightBarContent,
    setUploadDataloader,
  } = useDatasetsAndNotebooks();

  const navigate = useNavigate();
  const { dataloaderName } = useParams();
  const step = dataloaderName ? 1 : 0;

  const [selectedLoader, setSelectedLoader] = useState();
  const [loaders, setLoaders] = useState([]);
  const [loadingLoaders, setLoadingLoaders] = useState(true);
  const [formValues, setFormValues] = useState({});
  const [formHasErrors, setFormHasErrors] = useState(false);
  const [, setPreviewError] = useState(false);
  const [computeMetadata, setComputeMetadata] = useState(true);

  const { t } = useTranslation(["datasets"]);
  const { enqueueSnackbar } = useSnackbar();
  const tourContext = useTourContext();

  const formSubmitRef = useRef(null);

  const dataKind = useMemo(
    () => (selectedLoader ? loaderDataKind(selectedLoader) : null),
    [selectedLoader],
  );

  useEffect(() => {
    let cancelled = false;
    setLoadingLoaders(true);
    getComponentsRequest({ selectTypes: ["DataLoader"] })
      .then((list) => {
        if (!cancelled) setLoaders(list);
      })
      .catch(() => {
        if (!cancelled) {
          enqueueSnackbar(t("datasets:error.fetchingDataloaders"), {
            variant: "error",
          });
        }
      })
      .finally(() => {
        if (!cancelled) setLoadingLoaders(false);
      });
    return () => {
      cancelled = true;
    };
  }, [t, enqueueSnackbar]);

  // Sync selected loader from URL param, or redirect if unknown
  useEffect(() => {
    if (!dataloaderName || loadingLoaders || loaders.length === 0) return;
    const match = loaders.find((loader) => loader.name === dataloaderName);
    if (match) {
      setSelectedLoader(match);
    } else {
      navigate(UPLOAD_BASE_PATH, { replace: true });
    }
  }, [dataloaderName, loadingLoaders, loaders, navigate]);

  // Sync selected loader to context so DataBreadcrumbs can show display_name
  useEffect(() => {
    setUploadDataloader(selectedLoader?.name ? selectedLoader : null);
  }, [selectedLoader, setUploadDataloader]);

  // Clear right sidebar and loader on unmount
  useEffect(
    () => () => {
      setRightBarContent(null);
      setUploadDataloader(null);
    },
    [setRightBarContent, setUploadDataloader],
  );

  // Update the right sidebar based on current step and data kind
  useEffect(() => {
    if (step === 0) {
      setRightBarContent(<ComponentDetailsPanel component={selectedLoader} />);
      return;
    }
    if (!selectedLoader?.name) {
      setRightBarContent(null);
      return;
    }
    if (dataKind === "document") {
      setRightBarContent(
        <DocumentLoaderConfigBar
          loaderName={selectedLoader.name}
          formSubmitRef={formSubmitRef}
          setError={setFormHasErrors}
        />,
      );
      return;
    }
    setRightBarContent(
      <DataloaderConfigBar
        selectedDataloader={selectedLoader.name}
        formSubmitRef={formSubmitRef}
        setError={setFormHasErrors}
        onValuesChange={setFormValues}
        computeMetadata={computeMetadata}
        onComputeMetadataChange={setComputeMetadata}
      />,
    );
  }, [step, selectedLoader, dataKind, setRightBarContent, computeMetadata]);

  const goToNextStep = () => {
    navigate(`${UPLOAD_BASE_PATH}/${selectedLoader.name}`);
  };

  const goToPrevStep = () => {
    if (step === 0) {
      backHome();
      return;
    }
    navigate(UPLOAD_BASE_PATH);
  };

  const getTitle = () => {
    if (step === 0) return t("datasets:label.selectDataloader");
    return dataKind === "document"
      ? t("datasets:document.uploadDocumentTitle")
      : t("datasets:label.uploadDataset");
  };

  const getSubtitle = () => {
    if (step === 0) return t("datasets:label.selectUploadMethod");
    return dataKind === "document"
      ? t("datasets:document.uploadAndConfigure")
      : t("datasets:label.uploadAndConfigure");
  };

  const handleDatasetCreated = (newDataset, datasetJob) => {
    addDatasetOptimistically(newDataset);
    setRightBarContent(null);
    startDatasetPolling(newDataset, datasetJob);
    navigate(`/app/data/datasets/${newDataset.id}`);

    if (tourContext?.run) {
      tourContext.completeTour();
      sessionStorage.setItem("startDatasetViewTour", "true");
    }
  };

  const handleDocumentCreated = (created, job) => {
    addDocumentOptimistically(created);
    setRightBarContent(null);
    startDocumentPolling(created, job);
    navigate(`/app/data/documents/${created.id}`);
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
          selectedDataloader={selectedLoader}
          setSelectedDataloader={setSelectedLoader}
          dataloaders={loaders}
          loadingDataloaders={loadingLoaders}
        />
      )}

      {step === 1 && selectedLoader?.name && dataKind === "dataset" && (
        <ConfigureAndUploadDatasetStep
          goToPrevStep={goToPrevStep}
          selectedDataloader={selectedLoader}
          backHome={backHome}
          handleDatasetCreated={handleDatasetCreated}
          formSubmitRef={formSubmitRef}
          formValues={formValues}
          onPreviewError={setPreviewError}
          formHasErrors={formHasErrors}
          existingDatasets={datasets}
          computeMetadata={computeMetadata}
        />
      )}

      {step === 1 && selectedLoader?.name && dataKind === "document" && (
        <ConfigureAndUploadDocumentStep
          selectedLoader={selectedLoader}
          goToPrevStep={goToPrevStep}
          backHome={backHome}
          formSubmitRef={formSubmitRef}
          formHasErrors={formHasErrors}
          existingDocuments={documents}
          onDocumentCreated={handleDocumentCreated}
        />
      )}
    </Box>
  );
}

UploadDataSteps.propTypes = {
  backHome: PropTypes.func.isRequired,
};
