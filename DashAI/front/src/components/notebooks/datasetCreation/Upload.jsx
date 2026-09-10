import React, {
  useCallback,
  useRef,
  useState,
  useMemo,
  useEffect,
} from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  CircularProgress,
  Grid,
  Typography,
  useTheme,
} from "@mui/material";

import PreviewDataset from "./PreviewDataset";

import { useSnackbar } from "notistack";
import JSZip from "jszip";
import { useTranslation } from "react-i18next";
import { useTourContext } from "../../tour/TourProvider";

/**
 * Renders a drag and drop to upload a file (dataset).
 * The upload (send to API) doesn't happen here, this component just adds the file "uploaded" to the
 * newDataset state in the modal
 * @param {function} onFileUpload function to handle when the user "uploads" a dataset
 * @param {File} initialFile optional initial file to display (when coming back from preview)
 * @param {object} formValues current form values from the configuration form
 * @param {function} onPreviewError callback to notify parent of preview errors
 * @param {function} onTypesChanged callback to notify parent when column types change
 * @param {function} onColumnRename callback to notify parent when columns are renamed
 * @param {function} onPreviewLoaded callback to notify parent when preview is loaded
 */
function Upload({
  onFileUpload,
  initialFile = null,
  formValues = {},
  selectedDataloader = null,
  onPreviewError,
  onTypesChanged,
  onColumnRename,
  onPreviewLoaded,
  onPreviewMetrics,
}) {
  const [EMPTY, LOADING, LOADED] = [0, 1, 2];
  const [datasetState, setDatasetState] = useState(
    initialFile ? LOADED : EMPTY,
  );
  const [dragActive, setDragActive] = useState(false);
  const [file, setFile] = useState(initialFile);
  const inputRef = useRef(null);
  const uploadGridRef = useRef(null);

  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const tourContext = useTourContext();

  // Monitor upload-area size changes to recalculate tour positioning
  useEffect(() => {
    if (!uploadGridRef.current || !tourContext?.run) return;

    const resizeObserver = new ResizeObserver(() => {
      // Dispatch resize event to force Joyride to recalculate positioning
      window.dispatchEvent(new Event("resize"));
    });

    resizeObserver.observe(uploadGridRef.current);
    return () => resizeObserver.disconnect();
  }, [tourContext?.run]);

  const uploadDataset = async (file) => {
    setDatasetState(LOADING);
    const url = "";
    onFileUpload(file, url);
    setDatasetState(LOADED);
    setFile(file);
  };

  // helper to extract allowed extensions from acceptAttr (returns lowercase extensions like ".csv")
  const getAllowedExtensions = (accept) => {
    if (!accept) return [];
    const parts = accept.split(",").map((p) => p.trim().toLowerCase());
    const exts = [];
    for (const p of parts) {
      if (p.startsWith(".")) exts.push(p);
      else if (p.endsWith("/*")) {
        // common mappings for wildcards when inspecting zips
        const major = p.split("/")[0];
        if (major === "image")
          exts.push(".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp");
      }
      // ignore explicit mime types for zip-inspection
    }
    return exts;
  };

  // helper to check file against acceptAttr (allows extensions like .csv and types like image/*)
  // for regular files it's synchronous; zip inspection is asynchronous and handled separately
  const isAcceptedFile = (file) => {
    if (!file) return false;
    if (!acceptAttr) return true; // no restriction

    const parts = acceptAttr.split(",").map((p) => p.trim().toLowerCase());
    const name = (file.name || "").toLowerCase();
    const type = (file.type || "").toLowerCase();

    for (const part of parts) {
      if (part.startsWith(".")) {
        if (name.endsWith(part)) return true;
      } else if (part.endsWith("/*")) {
        // image/* etc. compare major type
        const major = part.split("/")[0];
        if (type.startsWith(major + "/")) return true;
      } else {
        // direct mime type
        if (type === part) return true;
      }
    }

    // if it's a zip but acceptAttr includes .zip, we defer to zip-inspection elsewhere
    if (name.endsWith(".zip") && parts.includes(".zip")) return true;

    return false;
  };

  // validate ZIP contents asynchronously: returns true if at least one file inside the zip
  // matches one of the allowed internal extensions for the current dataloader
  const validateZipContents = async (file) => {
    try {
      const allowedExts = getAllowedExtensions(acceptAttr);
      if (!allowedExts || allowedExts.length === 0) {
        // if no explicit allowed extensions, accept any zip
        return true;
      }

      const arrayBuffer = await file.arrayBuffer();
      const zip = await JSZip.loadAsync(arrayBuffer);

      let found = false;
      zip.forEach((relativePath, zipEntry) => {
        if (found) return; // short-circuit
        if (zipEntry.dir) return; // skip directories
        const lower = relativePath.toLowerCase();
        for (const ext of allowedExts) {
          if (lower.endsWith(ext)) {
            found = true;
            break;
          }
        }
      });

      return found;
    } catch (err) {
      // If zip can't be read, treat as invalid
      enqueueSnackbar(t("datasets:error.loadingDatasetPreview"), {
        variant: "error",
      });
      console.error("Error reading zip for validation:", err);
      return false;
    }
  };

  const handleDrag = (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState === EMPTY) {
      if (e.type === "dragenter" || e.type === "dragover") {
        setDragActive(true);
      } else if (e.type === "dragleave") {
        setDragActive(false);
      }
    }
  };

  const handleSelect = async (e) => {
    if (datasetState !== EMPTY && datasetState !== LOADED) return;

    const f = e.target.files && e.target.files[0];
    if (!f) return;

    // fast check based on filename/mime
    if (!isAcceptedFile(f)) {
      enqueueSnackbar(t("datasets:error.fileTypeNotAllowed"), {
        variant: "error",
      });
      // clear input so the same file can be selected again later
      if (inputRef && inputRef.current) inputRef.current.value = "";
      return;
    }

    // if it's a zip, do a deeper inspection
    const name = (f.name || "").toLowerCase();
    if (name.endsWith(".zip")) {
      const ok = await validateZipContents(f);
      if (!ok) {
        enqueueSnackbar(t("datasets:error.zipContentsNotCompatible"), {
          variant: "error",
        });
        if (inputRef && inputRef.current) inputRef.current.value = "";
        return;
      }
    }

    uploadDataset(f);
  };

  const handleDrop = async (e) => {
    e.preventDefault();
    e.stopPropagation();
    if (datasetState !== EMPTY) return;

    setDragActive(false);
    const f = e.dataTransfer.files && e.dataTransfer.files[0];
    if (!f) return;

    if (!isAcceptedFile(f)) {
      enqueueSnackbar(t("datasets:error.fileTypeNotAllowed"), {
        variant: "error",
      });
      return;
    }

    const name = (f.name || "").toLowerCase();
    if (name.endsWith(".zip")) {
      const ok = await validateZipContents(f);
      if (!ok) {
        enqueueSnackbar(t("datasets:error.zipContentsNotCompatible"), {
          variant: "error",
        });
        return;
      }
    }

    uploadDataset(f);
  };

  const handleButtonClick = () => {
    inputRef.current.click();
  };

  const handleDeleteDataset = useCallback(() => {
    onFileUpload(null, "");
    setDatasetState(EMPTY);
    setFile(null);
  }, [onFileUpload]);

  // memoize datasetData object so its reference stays stable across renders.
  // `compute_metadata` is intentionally stripped: it only affects the upload
  // job, not the preview, so toggling it must not trigger a preview re-fetch.
  const datasetDataMemo = useMemo(() => {
    let dataloaderName = selectedDataloader;
    if (selectedDataloader && typeof selectedDataloader === "object") {
      dataloaderName =
        selectedDataloader.name || selectedDataloader.display_name || null;
    }

    // eslint-disable-next-line no-unused-vars
    const { compute_metadata, ...previewFormValues } = formValues || {};

    const params = {
      ...previewFormValues,
      inference_rows:
        previewFormValues.inference_rows != null
          ? previewFormValues.inference_rows
          : 1000,
      ...(dataloaderName ? { dataloader_name: dataloaderName } : {}),
    };

    return {
      file,
      params,
    };
  }, [file, formValues, selectedDataloader]);

  const acceptAttr = useMemo(() => {
    if (!selectedDataloader) return undefined;

    const extensions =
      typeof selectedDataloader === "object"
        ? selectedDataloader.metadata?.supported_extensions
        : undefined;

    if (!extensions || extensions.length === 0) return undefined;
    return extensions.join(",");
  }, [selectedDataloader]);

  // renders content inside the drag and drop component depending on the state of the dataset
  const stateContent = useCallback(
    (state) => {
      switch (state) {
        case EMPTY:
          return (
            <React.Fragment>
              {dragActive ? (
                <Grid>
                  <Typography
                    variant="subtitle1"
                    sx={{ color: theme.palette.text.secondary }}
                  >
                    {t("datasets:label.clickToUpload")}
                  </Typography>
                </Grid>
              ) : (
                <React.Fragment>
                  <Grid>
                    <Typography
                      variant="subtitle1"
                      sx={{ color: theme.palette.text.secondary }}
                    >
                      {t("datasets:label.dragAndDropFileHere")}
                    </Typography>
                  </Grid>
                  <Grid>
                    <Button
                      variant="contained"
                      onClick={(e) => {
                        e.stopPropagation();
                        handleButtonClick();
                      }}
                    >
                      {t("datasets:button.uploadFile")}
                    </Button>
                  </Grid>
                </React.Fragment>
              )}
            </React.Fragment>
          );

        case LOADING:
          return <CircularProgress color="inherit" />;

        case LOADED:
          return (
            <Box
              sx={{
                width: "100%",
                height: "100%",
                display: "flex",
                flexDirection: "column",
              }}
            >
              <PreviewDataset
                datasetData={datasetDataMemo}
                onChangeDataset={(e) => {
                  e.stopPropagation();
                  inputRef.current?.click();
                }}
                onPreviewError={onPreviewError}
                onTypesChanged={onTypesChanged}
                onColumnRename={onColumnRename}
                onPreviewLoaded={onPreviewLoaded}
                onPreviewMetrics={onPreviewMetrics}
              />
            </Box>
          );
      }
    },
    [
      handleSelect,
      datasetDataMemo,
      onPreviewError,
      handleDeleteDataset,
      dragActive,
      handleButtonClick,
      acceptAttr,
      onTypesChanged,
    ],
  );

  return (
    <Grid
      ref={uploadGridRef}
      container
      direction="column"
      rowSpacing={4}
      sx={{
        width: "100%",
        bgcolor: theme.palette.ui.box,
        p: 8,
        borderRadius: 2,
      }}
      data-tour="upload-area"
    >
      {/* state text */}
      <Grid sx={{ textAlign: "center" }}>
        <Box sx={{ color: theme.palette.text.primary }}>
          {datasetState === EMPTY && t("datasets:label.uploadYourDataset")}
          {datasetState === LOADING && t("datasets:label.datasetLoading")}
          {datasetState === LOADED && t("datasets:label.datasetPreview")}
          {datasetState === EMPTY && (
            <Typography variant="body2" component="div">
              {t("datasets:label.ifYourDatasetHaveSplits")}
            </Typography>
          )}
        </Box>
      </Grid>

      <input
        type="file"
        ref={inputRef}
        style={{ display: "none" }}
        onChange={handleSelect}
        {...(acceptAttr ? { accept: acceptAttr } : {})}
      />

      {/* Drag and drop */}
      <Grid sx={{ width: "100%", display: "flex", justifyContent: "center" }}>
        <Box
          sx={{
            ...(datasetState === LOADED
              ? {}
              : {
                  border: 1,
                  borderWidth: 1,
                  borderStyle: "dashed",
                }),
            ...(datasetState === LOADED
              ? { minHeight: "33vh" }
              : { height: "33vh" }),
            width: datasetState === LOADED ? "100%" : "60%",
            maxWidth: datasetState === LOADED ? "100%" : "600px",
            borderRadius: 2,
            cursor: datasetState === EMPTY ? "pointer" : "auto",
            overflow: datasetState === LOADED ? "visible" : "auto",
            position: "relative",
            display: "flex",
          }}
          // blocks the upload of a new file if the file state is not empty
          onClick={datasetState === EMPTY ? handleButtonClick : null}
          onDragEnter={datasetState === EMPTY ? handleDrag : null}
          onDragLeave={datasetState === EMPTY ? handleDrag : null}
          onDragOver={datasetState === EMPTY ? handleDrag : null}
          onDrop={datasetState === EMPTY ? handleDrop : null}
        >
          <Grid
            container
            rowSpacing={4}
            direction="column"
            alignItems="center"
            justifyContent="center"
            sx={{
              height: datasetState === LOADED ? "auto" : "100%",
              width: "100%",
              flex: 1,
            }}
          >
            {/* Content inside the drag and drop that depends on the state */}
            {stateContent(datasetState)}
          </Grid>
        </Box>
      </Grid>
    </Grid>
  );
}

Upload.propTypes = {
  onFileUpload: PropTypes.func.isRequired,
  initialFile: PropTypes.object,
  formSubmitRef: PropTypes.object,
  formValues: PropTypes.object,
  selectedDataloader: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  onPreviewError: PropTypes.func,
  onTypesChanged: PropTypes.func,
  onColumnRename: PropTypes.func,
  onPreviewLoaded: PropTypes.func,
  onPreviewMetrics: PropTypes.func,
};

export default Upload;
