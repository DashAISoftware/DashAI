import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import {
  Box,
  Button,
  CircularProgress,
  List,
  ListItemButton,
  ListItemText,
  TextField,
  Typography,
} from "@mui/material";
import InsertDriveFileIcon from "@mui/icons-material/InsertDriveFile";
import HubBreadcrumbs from "./HubBreadcrumbs";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { createDataset } from "../../api/datasets";
import {
  createDocument,
  deleteDocument,
  enqueueHubDocumentJob,
} from "../../api/documents";
import { forceRefreshNow } from "../../utils/jobPoller";
import {
  importHubDataset,
  listDatafileFiles,
  previewHubDataset,
} from "../../api/hub";
import { useDatasetsAndNotebooks } from "../custom/contexts/DatasetsAndNotebooksContext";
import { getNextAvailableName } from "../../utils/nameGenerator";
import { getComponents } from "../../api/component";
import ComponentSelector from "../custom/ComponentSelector";
import PreviewDataset from "../notebooks/datasetCreation/PreviewDataset";
import { loadsDataKind } from "../../utils/dataKinds";
import { useTourContext } from "../tour/TourProvider";
import { isTourAtTarget, useTourStageSync } from "../tour/tourUtils";

// File and DataLoader the hub import tour points to (the scikit-learn/iris
// download from HuggingFace ships Iris.csv next to a SQLite copy).
const TOUR_FILE = "Iris.csv";
const TOUR_DATALOADER = "CSVDataLoader";
const isTourFile = (f) => f.split(/[\\/]/).pop() === TOUR_FILE;
const fileBaseName = (f) => f.split(/[\\/]/).pop();

function documentLoaderSupportsFile(loader, file) {
  const extensions = loader?.metadata?.supported_extensions || [];
  if (extensions.length === 0) return true;
  const lower = file.toLowerCase();
  return extensions.some((extension) => lower.endsWith(extension));
}

/**
 * Full-page import panel for Hub datasets.
 *
 * Without datafile: step 0 = dataloader, step 1 = preview
 * With datafile:    step 0 = file select, step 1 = dataloader, step 2 = preview
 */
export default function HubImportPanel({
  dataset,
  sourceName,
  datafile = null,
  step,
  onStepChange,
  selectedLoader,
  onSelectedLoaderChange,
  formValues = {},
  formSubmitRef = null,
  formHasErrors = false,
  onCancel,
  onImported,
  onDocumentImported,
  computeMetadata = true,
}) {
  const { t } = useTranslation(["hub", "common", "datasets"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const { datasets, documents } = useDatasetsAndNotebooks();
  const [localStep, setLocalStep] = useState(0);
  const [localSelectedLoader, setLocalSelectedLoader] = useState(null);
  const stepValue = step ?? localStep;
  const setStepValue = onStepChange ?? setLocalStep;
  const selectedValue = selectedLoader ?? localSelectedLoader;
  const isDocument = loadsDataKind(selectedValue, "document");

  // Whether datafile flow adds an extra file-select step at position 0
  const hasFileStep = datafile != null;
  // Adjusted step indices for dataloader / preview
  const dataloaderStep = hasFileStep ? 1 : 0;
  const previewStep = hasFileStep ? 2 : 1;

  const [dataloaders, setDataloaders] = useState([]);
  const [loadingDataloaders, setLoadingDataloaders] = useState(false);

  // File picker state
  const [files, setFiles] = useState([]);
  const [loadingFiles, setLoadingFiles] = useState(false);
  const [selectedFile, setSelectedFile] = useState(null);

  const [name, setName] = useState("");
  const [previewData, setPreviewData] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(false);
  const [columnTypes, setColumnTypes] = useState({});
  const [columnRenames, setColumnRenames] = useState({});
  const [importing, setImporting] = useState(false);
  const previewDebounceRef = useRef(null);
  const tourContext = useTourContext();
  useTourStageSync(tourContext, stepValue);

  // Load DataLoaders when entering the dataloader-selector step
  useEffect(() => {
    if (stepValue !== dataloaderStep) return;
    let isMounted = true;
    setLoadingDataloaders(true);
    getComponents({ selectTypes: ["DataLoader"] })
      .then((infos) => {
        if (isMounted) setDataloaders(infos);
      })
      .catch(() => {
        if (isMounted) setDataloaders([]);
      })
      .finally(() => {
        if (isMounted) setLoadingDataloaders(false);
      });
    return () => {
      isMounted = false;
    };
  }, [stepValue, dataloaderStep]);

  // Reset when dataset/source changes
  useEffect(() => {
    if (!dataset || !sourceName) return;
    setName(dataset.name || "");
    setLocalSelectedLoader(null);
    setPreviewData(null);
    setPreviewError(false);
    setColumnTypes({});
    setColumnRenames({});
    setSelectedFile(null);
    setFiles([]);
  }, [dataset?.id, sourceName]);

  // Load files when entering file-select step
  useEffect(() => {
    if (!hasFileStep || stepValue !== 0 || !datafile) return;
    let isMounted = true;
    setLoadingFiles(true);
    listDatafileFiles(datafile.id)
      .then((f) => {
        if (!isMounted) return;
        setFiles(f);
        if (f.length === 1) setSelectedFile(f[0]);
      })
      .catch(() => {
        if (isMounted) setFiles([]);
      })
      .finally(() => {
        if (isMounted) setLoadingFiles(false);
      });
    return () => {
      isMounted = false;
    };
  }, [hasFileStep, stepValue, datafile?.id]);

  const availableLoaders = useMemo(
    () =>
      dataloaders.filter((component) =>
        loadsDataKind(component, "document")
          ? !!datafile &&
            !!selectedFile &&
            documentLoaderSupportsFile(component, selectedFile)
          : loadsDataKind(component, "dataset"),
      ),
    [dataloaders, datafile, selectedFile],
  );

  // Preview
  useEffect(() => {
    if (stepValue !== previewStep || !dataset || !sourceName || isDocument)
      return;

    let isMounted = true;
    if (previewDebounceRef.current) clearTimeout(previewDebounceRef.current);

    setPreviewData(null);
    setPreviewLoading(true);
    setPreviewError(false);

    const rows = Number(formValues?.inference_rows);
    const effectiveRows = Number.isFinite(rows)
      ? Math.min(Math.max(2, rows), 500)
      : 100;

    // eslint-disable-next-line no-unused-vars
    const { compute_metadata, ...previewFormValues } = formValues || {};
    previewDebounceRef.current = setTimeout(() => {
      previewHubDataset(
        sourceName,
        dataset.id,
        effectiveRows,
        selectedValue?.name,
        previewFormValues,
        datafile?.id,
        selectedFile ?? undefined,
      )
        .then((data) => {
          if (!isMounted) return;
          setPreviewData(data);
          setColumnTypes(data.inferred_types || {});
        })
        .catch(() => {
          if (isMounted) setPreviewError(true);
        })
        .finally(() => {
          if (isMounted) setPreviewLoading(false);
        });
    }, 350);

    return () => {
      isMounted = false;
      if (previewDebounceRef.current) clearTimeout(previewDebounceRef.current);
    };
  }, [
    stepValue,
    previewStep,
    isDocument,
    dataset?.id,
    sourceName,
    selectedValue?.name,
    datafile?.id,
    selectedFile,
    // Exclude compute_metadata from the dep — it doesn't affect the preview
    // and toggling it must not re-fetch.
    JSON.stringify(
      (() => {
        // eslint-disable-next-line no-unused-vars
        const { compute_metadata, ...rest } = formValues || {};
        return rest;
      })(),
    ),
  ]);

  const handleColumnRename = useCallback((oldName, newName) => {
    setColumnRenames((prev) => ({ ...prev, [oldName]: newName }));
  }, []);

  const createDocumentWithFreeName = async (payload) => {
    try {
      return await createDocument(payload);
    } catch (error) {
      if (error?.response?.status !== 409) throw error;
      const nextName = getNextAvailableName(payload.name, documents);
      setName(nextName);
      return createDocument({ ...payload, name: nextName });
    }
  };

  const handleDocumentImport = async () => {
    if (!name.trim() || !datafile || !selectedFile || !selectedValue) return;
    if (formHasErrors) return;
    setImporting(true);
    try {
      const created = await createDocumentWithFreeName({
        name: name.trim(),
        file_name: fileBaseName(selectedFile),
        dataloader: selectedValue.name,
        dataloader_params: formSubmitRef?.current?.values || {},
      });
      let job;
      try {
        job = await enqueueHubDocumentJob(
          created.id,
          created.name,
          datafile.id,
          selectedFile,
        );
      } catch (enqueueError) {
        await deleteDocument(created.id).catch(() => {});
        throw enqueueError;
      }
      forceRefreshNow();
      enqueueSnackbar(t("hub:importSuccess"), { variant: "success" });
      onDocumentImported?.(created, job);
    } catch (error) {
      const detail = error?.response?.data?.detail;
      enqueueSnackbar(
        typeof detail === "string" ? detail : t("hub:importError"),
        { variant: "error" },
      );
    } finally {
      setImporting(false);
    }
  };

  const handleImport = async () => {
    if (isDocument) {
      await handleDocumentImport();
      return;
    }
    if (!name.trim() || !dataset || !selectedValue || formHasErrors) return;
    setImporting(true);
    try {
      let effectiveName = name.trim();
      let created;
      try {
        created = await createDataset(effectiveName);
      } catch (createError) {
        if (createError?.response?.status === 409) {
          effectiveName = getNextAvailableName(effectiveName, datasets);
          setName(effectiveName);
          created = await createDataset(effectiveName);
        } else {
          throw createError;
        }
      }

      // eslint-disable-next-line no-unused-vars
      const { compute_metadata, ...dataloaderParams } = formValues || {};
      const importParams = {
        dataloader: selectedValue.name,
        dataloader_params: dataloaderParams,
        inferred_types: columnTypes,
        column_renames: columnRenames,
        compute_metadata: computeMetadata,
      };
      if (datafile) {
        importParams.datafile_id = datafile.id;
        if (selectedFile) importParams.selected_file = selectedFile;
      }
      const importResult = await importHubDataset(
        sourceName,
        dataset.id,
        created.id,
        importParams,
      );
      enqueueSnackbar(t("hub:importSuccess"), { variant: "success" });
      if (isTourAtTarget(tourContext, "hub-import-button")) {
        tourContext.markTourAsCompleted();
        tourContext.stopTour();
      }
      onImported?.(created, importResult);
    } catch {
      enqueueSnackbar(t("hub:importError"), { variant: "error" });
    } finally {
      setImporting(false);
    }
  };

  const canProceedFromFile =
    hasFileStep && stepValue === 0 ? !!selectedFile : true;
  const canProceed =
    stepValue === dataloaderStep ? !!selectedValue?.name : canProceedFromFile;
  const canImport =
    !!selectedValue?.name &&
    !!name.trim() &&
    !formHasErrors &&
    !importing &&
    (isDocument
      ? !!datafile && !!selectedFile
      : !previewLoading && !previewError && !!previewData);

  const handleBack = () => setStepValue((s) => s - 1);
  const handleNext = () => setStepValue((s) => s + 1);

  return (
    <Box
      sx={{ height: "100%", display: "flex", flexDirection: "column", p: 4 }}
    >
      <Box>
        <HubBreadcrumbs
          crumbs={[
            {
              label: t("hub:title"),
              onClick: () => navigate("/app/data/hub"),
            },
            ...(dataset?.name
              ? [
                  {
                    label: sourceName
                      ? `${dataset.name} (${sourceName})`
                      : dataset.name,
                    ...(stepValue > 0
                      ? { onClick: () => setStepValue(0) }
                      : {}),
                  },
                ]
              : []),
            ...(stepValue >= dataloaderStep
              ? [
                  {
                    label: t("hub:stepDataloaderTitle"),
                    ...(stepValue > dataloaderStep
                      ? { onClick: () => setStepValue(dataloaderStep) }
                      : {}),
                  },
                ]
              : []),
            ...(stepValue >= previewStep && selectedValue
              ? [{ label: selectedValue.display_name || selectedValue.name }]
              : []),
          ]}
          onBack={() =>
            sourceName
              ? navigate(`/app/data/hub/${sourceName}`)
              : navigate("/app/data/hub")
          }
        />
      </Box>

      <Box sx={{ p: 2, flex: 1, overflowY: "auto" }}>
        {/* Step 0 (with hubDownload): file selector */}
        {hasFileStep && stepValue === 0 && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box>
              <Typography variant="h5" component="h1">
                {t("hub:stepFileTitle")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hub:stepFileSubtitle")}
              </Typography>
            </Box>

            {loadingFiles ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                <CircularProgress />
              </Box>
            ) : files.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t("hub:noFilesFound")}
              </Typography>
            ) : (
              <List disablePadding>
                {files.map((f) => (
                  <ListItemButton
                    key={f}
                    selected={selectedFile === f}
                    onClick={() => {
                      setSelectedFile(f);
                      if (
                        isTourFile(f) &&
                        isTourAtTarget(tourContext, "hub-example-file")
                      ) {
                        tourContext.nextStep();
                      }
                    }}
                    data-tour={
                      tourContext?.run && isTourFile(f)
                        ? "hub-example-file"
                        : undefined
                    }
                    sx={{ borderRadius: 1, mb: 0.5 }}
                  >
                    <InsertDriveFileIcon
                      sx={{ mr: 1, fontSize: 18, color: "text.secondary" }}
                    />
                    <ListItemText
                      primary={f}
                      primaryTypographyProps={{
                        variant: "body2",
                        fontFamily: "monospace",
                      }}
                    />
                  </ListItemButton>
                ))}
              </List>
            )}
          </Box>
        )}

        {/* Dataloader step */}
        {stepValue === dataloaderStep && (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              gap: 2,
              height: "100%",
              minHeight: 0,
            }}
          >
            <Box>
              <Typography variant="h5" component="h1">
                {t("hub:stepDataloaderTitle")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hub:stepDataloaderSubtitle")}
              </Typography>
            </Box>

            {loadingDataloaders ? (
              <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                <CircularProgress />
              </Box>
            ) : availableLoaders.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t("hub:noCompatibleDataloaders")}
              </Typography>
            ) : (
              <Box sx={{ flex: 1, minHeight: 0 }}>
                <ComponentSelector
                  components={availableLoaders}
                  selected={selectedValue}
                  onSelect={(item) => {
                    setLocalSelectedLoader(item);
                    onSelectedLoaderChange?.(item);
                    if (
                      item?.name === TOUR_DATALOADER &&
                      isTourAtTarget(
                        tourContext,
                        "hub-example-dataloader-option",
                      )
                    ) {
                      tourContext.nextStep();
                    }
                  }}
                  tourDataFor={
                    tourContext?.run ? "hub-example-dataloader-option" : null
                  }
                  tourDataMatchFn={(c) => c.name === TOUR_DATALOADER}
                  searchPlaceholder={t("datasets:searchDataloaders", {
                    defaultValue: "Search data loaders...",
                  })}
                />
              </Box>
            )}
          </Box>
        )}

        {stepValue === previewStep && isDocument && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box>
              <Typography variant="h5" component="h1">
                {t("hub:stepDocumentTitle")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hub:stepDocumentSubtitle")}
              </Typography>
            </Box>
            <TextField
              label={t("hub:documentName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
            />
            {selectedFile && (
              <Box sx={{ display: "flex", alignItems: "center" }}>
                <InsertDriveFileIcon
                  sx={{ mr: 1, fontSize: 18, color: "text.secondary" }}
                />
                <Typography variant="body2" sx={{ fontFamily: "monospace" }}>
                  {selectedFile}
                </Typography>
              </Box>
            )}
          </Box>
        )}

        {/* Preview step */}
        {stepValue === previewStep && !isDocument && (
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
            <Box>
              <Typography variant="h5" component="h1">
                {t("hub:stepPreviewTitle")}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {t("hub:stepPreviewSubtitle")}
              </Typography>
            </Box>
            <TextField
              label={t("hub:datasetName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              fullWidth
              data-tour="hub-dataset-name"
            />

            {previewLoading && (
              <Box sx={{ display: "flex", justifyContent: "center", py: 4 }}>
                <CircularProgress />
              </Box>
            )}

            {previewError && !previewLoading && (
              <Typography color="error">{t("hub:previewError")}</Typography>
            )}

            {!previewLoading && !previewError && previewData && (
              <Box data-tour="hub-preview-table">
                <PreviewDataset
                  initialData={previewData}
                  onTypesChanged={setColumnTypes}
                  onColumnRename={handleColumnRename}
                />
              </Box>
            )}
          </Box>
        )}
      </Box>

      <Box
        sx={{
          p: 2,
          borderTop: 1,
          borderColor: "divider",
          display: "flex",
          justifyContent: "space-between",
          gap: 1,
        }}
      >
        <Box sx={{ flexGrow: 1 }} />

        <Box sx={{ display: "flex", gap: 1 }}>
          {stepValue === 0 ? (
            <Button variant="outlined" onClick={onCancel}>
              {t("common:cancel")}
            </Button>
          ) : (
            <Button variant="outlined" onClick={handleBack}>
              {t("common:back")}
            </Button>
          )}
          {stepValue < previewStep ? (
            <Button
              variant="contained"
              onClick={handleNext}
              disabled={!canProceed}
              data-tour="hub-import-next-button"
            >
              {t("common:next")}
            </Button>
          ) : (
            <Button
              variant="contained"
              onClick={handleImport}
              disabled={!canImport}
              data-tour="hub-import-button"
            >
              {importing
                ? t("hub:importing")
                : isDocument
                  ? t("hub:importDocument")
                  : t("hub:importDataset")}
            </Button>
          )}
        </Box>
      </Box>
    </Box>
  );
}
