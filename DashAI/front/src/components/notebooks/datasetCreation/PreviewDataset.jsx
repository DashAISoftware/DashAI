import { useCallback, useEffect, useState, useRef } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Button,
  CircularProgress,
  Grid,
  IconButton,
  Tooltip,
  Typography,
} from "@mui/material";
import { UploadFile as UploadFileIcon } from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import { useSnackbar } from "notistack";
import { previewWithTypes } from "../../../api/datasets";
import PreviewDatasetTable from "./PreviewDatasetTable";
import { useTranslation } from "react-i18next";
import { estimateTotalRows } from "../../../utils/metadataRecommendation";

/**
 * This component shows a preview of the dataset before final upload.
 *
 * @param {object} datasetData - Object containing params, file, and url for the dataset
 * @param {function} onChangeDataset - Callback function when the user wants to change the dataset
 * @param {function} onPreviewError - Callback function to notify parent of preview errors
 * @param {function} onTypesChanged - Callback to notify parent when column types change
 * @param {function} onColumnRename - Callback to notify parent when columns are renamed (oldName, newName)
 * @param {function} onPreviewLoaded - Callback to notify parent when preview is loaded
 * @param {object} initialData - Pre-fetched preview data; when provided, skips the previewWithTypes API call
 */
function PreviewDataset({
  datasetData,
  onChangeDataset,
  onPreviewError,
  onTypesChanged,
  onColumnRename,
  onPreviewLoaded,
  initialData = null,
  onPreviewMetrics,
}) {
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const [previewData, setPreviewData] = useState(null);
  const [columnTypes, setColumnTypes] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const onTypesChangedRef = useRef(onTypesChanged);
  const { t } = useTranslation(["common", "datasets"]);

  useEffect(() => {
    onTypesChangedRef.current = onTypesChanged;
  }, [onTypesChanged]);

  useEffect(() => {
    if (onPreviewError) {
      onPreviewError(!!error);
    }
  }, [error, onPreviewError]);

  useEffect(() => {
    if (onPreviewLoaded && !loading && !error) {
      onPreviewLoaded();
    }
  }, [loading, error, onPreviewLoaded]);

  useEffect(() => {
    if (initialData) {
      setPreviewData(initialData);
      setColumnTypes(initialData.inferred_types);
      if (onTypesChangedRef.current) {
        onTypesChangedRef.current(initialData.inferred_types);
      }
      setError(null);
      setLoading(false);
      return;
    }

    const loadPreview = async () => {
      if (!datasetData) {
        setError(t("datasets:error.noDatasetDataAvailable"));
        setLoading(false);
        return;
      }

      try {
        setLoading(true);
        const { params, file } = datasetData;

        const formData = new FormData();
        formData.append("file", file);

        const previewParams = {
          inference_rows: 1000,
          ...params,
        };
        formData.append("params", JSON.stringify(previewParams));

        const result = await previewWithTypes(formData);
        setPreviewData(result);
        setColumnTypes(result.inferred_types);

        if (onTypesChangedRef.current) {
          onTypesChangedRef.current(result.inferred_types);
        }

        setError(null);
      } catch (err) {
        console.error("Error loading preview:", err);
        setError(t("datasets:error.loadingDatasetPreview"));
      } finally {
        setLoading(false);
      }
    };

    loadPreview();
    // Re-run preview when the file changes OR when params change. We stringify params to
    // create a stable dependency so changes to configuration in the right sidebar
    // trigger a new preview request.
  }, [
    initialData,
    datasetData?.file,
    JSON.stringify(datasetData?.params || {}),
  ]);

  const handleTypeChange = useCallback(
    (typeChanges) => {
      setColumnTypes((prevTypes) => {
        const updatedTypes = { ...prevTypes };

        Object.keys(typeChanges).forEach((columnName) => {
          const change = typeChanges[columnName];
          const prev = updatedTypes[columnName] || {};
          const updated = {
            ...prev,
            type: change.new_type,
            dtype: change.new_dtype,
          };
          // When changing to Categorical, set a default encoder if not already present
          if (change.new_type === "Categorical" && !updated.encoder) {
            updated.encoder =
              change.new_dtype === "int64" || change.new_dtype === "float64"
                ? "label"
                : "one_hot";
          }
          // When changing away from Categorical, drop encoder
          if (change.new_type !== "Categorical") {
            delete updated.encoder;
          }
          updatedTypes[columnName] = updated;
        });

        if (onTypesChangedRef.current) {
          onTypesChangedRef.current(updatedTypes);
        }

        return updatedTypes;
      });

      enqueueSnackbar(t("datasets:message.columnTypesUpdated"), {
        variant: "success",
      });
    },
    [enqueueSnackbar, onTypesChanged],
  );

  const handleEncoderChange = useCallback((columnName, newEncoder) => {
    setColumnTypes((prevTypes) => {
      const updatedTypes = {
        ...prevTypes,
        [columnName]: { ...prevTypes[columnName], encoder: newEncoder },
      };
      if (onTypesChangedRef.current) {
        onTypesChangedRef.current(updatedTypes);
      }
      return updatedTypes;
    });
  }, []);

  const handleColumnRename = useCallback(
    (oldName, newName) => {
      if (onColumnRename) {
        onColumnRename(oldName, newName);
      }
    },
    [onColumnRename],
  );

  const colCount = previewData
    ? Object.keys(previewData.inferred_types || previewData.schema || {}).length
    : 0;
  const estRows = previewData
    ? estimateTotalRows({
        previewRowCount: previewData.preview_row_count,
        previewedBytes: previewData.previewed_bytes,
        fileSize: datasetData?.file?.size ?? 0,
      })
    : 0;

  useEffect(() => {
    if (previewData && onPreviewMetrics) {
      onPreviewMetrics({ colCount, estRows });
    }
  }, [previewData, colCount, estRows, onPreviewMetrics]);

  return (
    <Grid
      sx={{
        borderRadius: 2,
        boxShadow: "none",
      }}
    >
      <Grid sx={{ p: 8 }}>
        {loading && (
          <Box
            sx={{
              display: "flex",
              justifyContent: "center",
              alignItems: "center",
              minHeight: "300px",
            }}
          >
            <CircularProgress />
          </Box>
        )}

        {error && !loading && (
          <Box
            sx={{
              border: 1,
              borderWidth: 1,
              borderStyle: "dashed",
              borderRadius: 2,
              height: "33vh",
              width: "60%",
              maxWidth: "600px",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
              margin: "0 auto",
            }}
          >
            <Typography color="error" variant="h6">
              {error}
            </Typography>
            <Button
              onClick={(e) => {
                e.stopPropagation();
                onChangeDataset(e);
              }}
              sx={{
                position: "absolute",
                top: 8,
                right: 8,
                minWidth: "auto",
                width: 32,
                height: 32,
                borderRadius: "50%",
                padding: 0,
                fontSize: "1.3rem",
                color: "text.secondary",
                "&:hover": {
                  backgroundColor: theme.palette.ui.hover,
                },
              }}
            >
              ✕
            </Button>
          </Box>
        )}

        {!loading && !error && previewData && (
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              width: "100%",
            }}
          >
            <Box
              sx={{
                display: "flex",
                justifyContent: "space-between",
                alignItems: "flex-start",
                gap: 4,
                mb: 4,
                flexShrink: 0,
              }}
            >
              <Typography variant="body2" color="text.secondary">
                {t(
                  previewData.types_inferred === false
                    ? "datasets:label.showingRowsPreview"
                    : "datasets:label.showingRowsInference",
                  {
                    sampleLength: previewData.sample.length,
                    previewRowCount: previewData.preview_row_count,
                  },
                )}
                <br />
                {t("datasets:label.changeColumnTypesInfo")}
              </Typography>

              {onChangeDataset && (
                <Tooltip title={t("datasets:button.reUploadDataset")}>
                  <IconButton
                    onClick={onChangeDataset}
                    size="small"
                    sx={{
                      flexShrink: 0,
                      border: `1px solid ${theme.palette.action.disabled}`,
                      borderRadius: 2,
                      color: "text.secondary",
                      padding: "4px",
                      transition: "color 0.2s, border-color 0.2s",
                      "&:hover": {
                        backgroundColor: "transparent",
                        color: "primary.main",
                        borderColor: theme.palette.primary.main,
                      },
                    }}
                  >
                    <UploadFileIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
            <Box sx={{ width: "100%" }}>
              <PreviewDatasetTable
                rows={previewData.sample}
                columnTypes={columnTypes}
                file={datasetData?.file ?? null}
                params={datasetData?.params ?? {}}
                onTypeChange={handleTypeChange}
                onColumnRename={handleColumnRename}
                onEncoderChange={handleEncoderChange}
              />
            </Box>
          </Box>
        )}
      </Grid>
    </Grid>
  );
}

PreviewDataset.propTypes = {
  datasetData: PropTypes.object,
  onChangeDataset: PropTypes.func,
  onPreviewError: PropTypes.func,
  onTypesChanged: PropTypes.func,
  onColumnRename: PropTypes.func,
  onPreviewLoaded: PropTypes.func,
  initialData: PropTypes.shape({
    sample: PropTypes.array.isRequired,
    inferred_types: PropTypes.object.isRequired,
    preview_row_count: PropTypes.number,
  }),
  onPreviewMetrics: PropTypes.func,
};

export default PreviewDataset;
