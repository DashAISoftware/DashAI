import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import { Box, Grid, TextField } from "@mui/material";
import Upload from "./Upload";
import { useSnackbar } from "notistack";
import { enqueueDatasetJob as enqueueDatasetRequest } from "../../../api/job";
import { forceRefreshNow } from "../../../utils/jobPoller";
import { useTourContext } from "../../tour/TourProvider";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../../utils/nameGenerator";
import { createDataset } from "../../../api/datasets";
import { useTranslation } from "react-i18next";
import { useTheme } from "@mui/material/styles";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import ComputeMetadataConfirmDialog from "../../datasets/ComputeMetadataConfirmDialog";
import { shouldRecommendDisableMetadata } from "../../../utils/metadataRecommendation";

export default function ConfigureAndUploadDatasetStep({
  selectedDataloader,
  goToPrevStep,
  backHome,
  handleDatasetCreated,
  formSubmitRef,
  formValues,
  onPreviewError,
  formHasErrors,
  existingDatasets = [],
  computeMetadata = true,
  onPreviewMetrics,
}) {
  const { defaultName } = useMemo(
    () => generateSequentialName({ base: "Dataset", items: existingDatasets }),
    [existingDatasets],
  );
  const [datasetName, setDatasetName] = useState("");
  const lastAutoFilledRef = useRef(null);
  const [uploadEnabled, setUploadEnabled] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [previewLoaded, setPreviewLoaded] = useState(false);
  const [datasetFileToUpload, setDatasetFileToUpload] = useState(null);
  const [columnTypes, setColumnTypes] = useState(null);
  const [columnRenames, setColumnRenames] = useState({});
  const [previewMetrics, setPreviewMetrics] = useState({
    colCount: 0,
    estRows: 0,
  });
  const [confirmOpen, setConfirmOpen] = useState(false);
  const tourContext = useTourContext();

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["common", "datasets"]);
  const theme = useTheme();

  useEffect(() => {
    if (!defaultName) return;
    if (!datasetName || datasetName === lastAutoFilledRef.current) {
      setDatasetName(defaultName);
      lastAutoFilledRef.current = defaultName;
    }
  }, [defaultName]);

  useEffect(() => {
    if (onPreviewError) {
      onPreviewError(previewError);
    }
  }, [previewError, onPreviewError]);

  useEffect(() => {
    if (previewError) {
      enqueueSnackbar(t("datasets:error.loadingDatasetPreview"), {
        variant: "error",
      });
    }
  }, [previewError, enqueueSnackbar]);

  const doSubmit = useCallback(
    async (effectiveComputeMetadata) => {
      if (!datasetFileToUpload || !datasetFileToUpload.file) {
        enqueueSnackbar(t("datasets:error.noDatasetFileAvailable"), {
          variant: "error",
        });
        return;
      }

      setUploading(true);

      try {
        // Safely read values from the form ref (may be undefined briefly)
        const refValues =
          formSubmitRef && formSubmitRef.current
            ? formSubmitRef.current.values || {}
            : {};
        // Merge values coming from the form schema and the onValuesChange callback
        const params = { ...refValues, ...(formValues || {}) };

        const name = datasetName.trim() || datasetFileToUpload.file.name;
        params["name"] = name;

        // Ensure dataloader is passed as a string (backend expects the dataloader name)
        let dataloaderName = selectedDataloader;
        if (selectedDataloader && typeof selectedDataloader === "object") {
          dataloaderName =
            selectedDataloader.name || selectedDataloader.display_name || null;
        }
        params["dataloader"] = dataloaderName;

        if (columnTypes) {
          params["inferred_types"] = columnTypes;
        }

        if (Object.keys(columnRenames).length > 0) {
          params["column_renames"] = columnRenames;
        }

        params["compute_metadata"] = effectiveComputeMetadata;

        const { file, url } = datasetFileToUpload;

        let effectiveName = name;
        let data;
        try {
          data = await createDataset(effectiveName);
        } catch (createError) {
          if (createError?.response?.status === 409) {
            effectiveName = getNextAvailableName(
              effectiveName,
              existingDatasets,
            );
            setDatasetName(effectiveName);
            params["name"] = effectiveName;
            data = await createDataset(effectiveName);
          } else {
            throw createError;
          }
        }

        try {
          const job = await enqueueDatasetRequest(data.id, file, url, params);
          forceRefreshNow();
          handleDatasetCreated(data, job);

          if (tourContext?.run) {
            tourContext.nextStep();
          }
        } catch (err) {
          console.error("Error enqueuing dataset job:", err);
          enqueueSnackbar(t("datasets:error.enqueueDatasetJob"), {
            variant: "error",
          });
          backHome();
        }
      } catch (error) {
        console.error("Error creating dataset:", error);
        enqueueSnackbar(t("datasets:error.createDatasetError"), {
          variant: "error",
        });
        backHome();
      } finally {
        setUploading(false);
      }
    },
    [
      selectedDataloader,
      datasetFileToUpload,
      datasetName,
      columnTypes,
      columnRenames,
      formSubmitRef,
      formValues,
      handleDatasetCreated,
      backHome,
      enqueueSnackbar,
      tourContext,
      t,
    ],
  );

  const submitNewDataset = useCallback(async () => {
    if (computeMetadata && shouldRecommendDisableMetadata(previewMetrics)) {
      setConfirmOpen(true);
      return;
    }
    await doSubmit(computeMetadata);
  }, [computeMetadata, previewMetrics, doSubmit]);

  const handlePreviewMetrics = useCallback(
    (metrics) => {
      setPreviewMetrics(metrics);
      if (onPreviewMetrics) {
        onPreviewMetrics(metrics);
      }
    },
    [onPreviewMetrics],
  );

  const handleFileUpload = (file, url) => {
    setDatasetFileToUpload({ file, url });
    setPreviewLoaded(false);
  };

  const handlePreviewLoaded = () => {
    setPreviewLoaded(true);
  };

  const handleTypesChanged = useCallback((types) => {
    setColumnTypes(types);
  }, []);

  const handleColumnRename = useCallback((oldName, newName) => {
    setColumnRenames((prev) => ({
      ...prev,
      [oldName]: newName,
    }));
  }, []);

  const isFormValid = () => {
    if (!formSubmitRef.current) return false;

    const formik = formSubmitRef.current;
    const hasErrors = formik.errors && Object.keys(formik.errors).length > 0;

    return !hasErrors && !formHasErrors;
  };

  useEffect(() => {
    if (
      datasetFileToUpload &&
      datasetFileToUpload.file !== null &&
      !previewError &&
      previewLoaded &&
      isFormValid()
    ) {
      setUploadEnabled(true);
    } else {
      setUploadEnabled(false);
    }
  }, [
    datasetFileToUpload,
    previewError,
    previewLoaded,
    formHasErrors,
    formValues,
  ]);

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        flex: 1,
        minHeight: 0,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <TextField
          label={t("datasets:label.datasetName")}
          value={datasetName}
          onChange={(e) => setDatasetName(e.target.value)}
          fullWidth
        />
      </Box>

      <Grid
        container
        direction="column"
        justifyContent="flex-start"
        alignItems="stretch"
        spacing={4}
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          width: "100%",
        }}
      >
        <Upload
          onFileUpload={handleFileUpload}
          formSubmitRef={formSubmitRef}
          onColumnRename={handleColumnRename}
          formValues={formValues}
          selectedDataloader={selectedDataloader}
          onPreviewError={setPreviewError}
          onTypesChanged={handleTypesChanged}
          onPreviewLoaded={handlePreviewLoaded}
          onPreviewMetrics={handlePreviewMetrics}
        />
      </Grid>

      <StepperNavigationFooter
        onBack={goToPrevStep}
        onNext={submitNewDataset}
        nextDisabled={!uploadEnabled}
        nextLabel={t("common:upload")}
        loading={uploading}
        nextDataTour={
          tourContext?.run ? "dataset-step-upload-button" : undefined
        }
      />
      <ComputeMetadataConfirmDialog
        open={confirmOpen}
        colCount={previewMetrics.colCount}
        estRows={previewMetrics.estRows}
        onConfirm={async () => {
          setConfirmOpen(false);
          await doSubmit(true);
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </Box>
  );
}
