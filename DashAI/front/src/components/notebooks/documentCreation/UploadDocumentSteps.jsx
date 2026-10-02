import { useEffect, useRef, useState } from "react";
import PropTypes from "prop-types";
import { useNavigate, useParams } from "react-router-dom";
import { Box, Typography } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import SelectDataloaderStep from "../datasetCreation/SelectDataloaderStep";
import ComponentDetailsPanel from "../../custom/ComponentDetailsPanel";
import ConfigureAndUploadDocumentStep from "./ConfigureAndUploadDocumentStep";
import DocumentLoaderConfigBar from "./DocumentLoaderConfigBar";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { getComponents as getComponentsRequest } from "../../../api/component";
import { loadsDataKind } from "../../../utils/dataKinds";

const UPLOAD_BASE_PATH = "/app/data/documents/new";

export default function UploadDocumentSteps({ backHome }) {
  const {
    documents,
    addDocumentOptimistically,
    startDocumentPolling,
    setRightBarContent,
    setUploadDataloader,
  } = useDatasetsAndNotebooks();
  const navigate = useNavigate();
  const { dataloaderName } = useParams();
  const step = dataloaderName ? 1 : 0;
  const { t } = useTranslation(["datasets"]);
  const { enqueueSnackbar } = useSnackbar();
  const formSubmitRef = useRef(null);
  const [loaders, setLoaders] = useState([]);
  const [loadingLoaders, setLoadingLoaders] = useState(true);
  const [selectedLoader, setSelectedLoader] = useState();
  const [formHasErrors, setFormHasErrors] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoadingLoaders(true);
    getComponentsRequest({ selectTypes: ["DataLoader"] })
      .then((list) => {
        if (!cancelled) {
          setLoaders(
            list.filter((component) => loadsDataKind(component, "document")),
          );
        }
      })
      .catch(() => {
        if (!cancelled) {
          enqueueSnackbar(t("datasets:document.fetchingLoaders"), {
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

  useEffect(() => {
    if (!dataloaderName || loadingLoaders || loaders.length === 0) return;
    const match = loaders.find((loader) => loader.name === dataloaderName);
    if (match) {
      setSelectedLoader(match);
    } else {
      navigate(UPLOAD_BASE_PATH, { replace: true });
    }
  }, [dataloaderName, loadingLoaders, loaders, navigate]);

  useEffect(() => {
    setUploadDataloader(selectedLoader?.name ? selectedLoader : null);
  }, [selectedLoader, setUploadDataloader]);

  useEffect(
    () => () => {
      setRightBarContent(null);
      setUploadDataloader(null);
    },
    [setRightBarContent, setUploadDataloader],
  );

  useEffect(() => {
    if (step === 0) {
      setRightBarContent(<ComponentDetailsPanel component={selectedLoader} />);
      return;
    }
    if (selectedLoader?.name) {
      setRightBarContent(
        <DocumentLoaderConfigBar
          loaderName={selectedLoader.name}
          formSubmitRef={formSubmitRef}
          setError={setFormHasErrors}
        />,
      );
    }
  }, [step, selectedLoader, setRightBarContent]);

  const goToNextStep = () =>
    navigate(`${UPLOAD_BASE_PATH}/${selectedLoader.name}`);

  const goToPrevStep = () => {
    if (step === 0) {
      backHome();
      return;
    }
    navigate(UPLOAD_BASE_PATH);
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
          {step === 0
            ? t("datasets:document.selectDocumentLoader")
            : t("datasets:document.uploadDocumentTitle")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {step === 0
            ? t("datasets:document.selectDocumentLoaderSubtitle")
            : t("datasets:document.uploadAndConfigure")}
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
      {step === 1 && selectedLoader?.name && (
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

UploadDocumentSteps.propTypes = {
  backHome: PropTypes.func.isRequired,
};
