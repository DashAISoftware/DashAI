import React, { useState, useCallback, useEffect } from "react";
import PropTypes from "prop-types";
import {
  Typography,
  IconButton,
  Box,
  Tooltip,
  CircularProgress,
} from "@mui/material";
import DeleteConfirmationModal from "../threeSectionLayout/DeleteConfirmationModal";
import RunStatusDot from "../shared/RunStatusDot";
import {
  Delete as DeleteIcon,
  Download as DownloadIcon,
} from "@mui/icons-material";
import { deletePrediction } from "../../api/predict";
import { useSnackbar } from "notistack";
import DatasetTable from "../notebooks/dataset/DatasetTable";
import {
  getDatasetFile,
  getDatasetFileFiltered,
  exportDatasetCsvByPath,
  getDatasetTypesByFilePath,
} from "../../api/datasets";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import {
  getTargetDecimals,
  formatPredictionRows,
} from "../../utils/predictionFormat";

const RUNNING_STATUSES = [1, 2]; // Delivered or Started

/**
 * PredictionCard - Displays a single prediction with results table
 */
export default function PredictionCard({
  prediction,
  onDelete,
  onUpdate,
  targetColumn = null,
  datasetSample = null,
  displayNumber = null,
}) {
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [columnTypes, setColumnTypes] = useState({});
  const theme = useTheme();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["prediction", "datasets", "common"]);

  // Fetch column types when results path changes
  useEffect(() => {
    if (!prediction?.results_path) return;
    getDatasetTypesByFilePath(prediction.results_path)
      .then(setColumnTypes)
      .catch(() => {});
  }, [prediction?.results_path]);

  const statusText = prediction.status;

  const isRunning = RUNNING_STATUSES.includes(statusText);
  const isFinished = statusText === 3; // Finished

  const handleDelete = async () => {
    try {
      await deletePrediction(prediction.id);
      enqueueSnackbar(t("prediction:message.deletedSuccessfully"), {
        variant: "success",
      });
      setDeleteDialogOpen(false);
      if (onDelete) onDelete();
    } catch (error) {
      console.error("Error deleting prediction:", error);
      enqueueSnackbar(t("prediction:error.errorDeleting"), {
        variant: "error",
      });
    }
  };

  const handleDownload = async () => {
    try {
      const blob = await exportDatasetCsvByPath(prediction.results_path);
      const isZip = blob.type === "application/zip";
      const ext = isZip ? "zip" : "csv";
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `prediction-${prediction.id}-${
          new Date(prediction.created).toISOString().split("T")[0]
        }.${ext}`,
      );
      document.body.appendChild(link);
      link.click();
      document.body.removeChild(link);
      URL.revokeObjectURL(url);
      enqueueSnackbar(t("prediction:message.downloadedSuccessfully"), {
        variant: "success",
      });
    } catch (error) {
      console.error("Error downloading prediction:", error);
      enqueueSnackbar(t("prediction:error.errorDownloading"), {
        variant: "error",
      });
    }
  };

  const fetchPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      if (!prediction.results_path) return { rows: [], total: 0 };
      const hasFilters =
        filterModel?.items?.length > 0 || (sortModel && sortModel.length > 0);
      const data = hasFilters
        ? await getDatasetFileFiltered(
            prediction.results_path,
            page,
            pageSize,
            filterModel,
            sortModel,
          )
        : await getDatasetFile(prediction.results_path, page, pageSize);
      const targetDecimals = getTargetDecimals(datasetSample, targetColumn);
      return {
        rows: formatPredictionRows(
          data.rows ?? [],
          targetColumn,
          targetDecimals,
        ),
        total: data.total ?? 0,
      };
    },
    [prediction.results_path, datasetSample, targetColumn],
  );

  return (
    <>
      <Box
        sx={{
          width: "100%",
          border: 1,
          borderColor: "divider",
          borderRadius: 1,
          bgcolor: "background.paper",
          p: 2,
        }}
      >
        {/* Header with status and dataset info */}
        <Box
          sx={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            mb: 2,
          }}
        >
          <Box sx={{ flex: 1, display: "flex", alignItems: "center", gap: 2 }}>
            <Typography
              variant="subtitle2"
              fontWeight="medium"
              sx={{ lineHeight: 1 }}
            >
              {t("prediction:label.prediction")} #
              {displayNumber ?? prediction.id}
            </Typography>
            <RunStatusDot status={statusText} />
          </Box>
          <Box sx={{ display: "flex", alignItems: "center", gap: 0.5 }}>
            <Tooltip title={t("prediction:button.downloadResults")}>
              <span>
                <IconButton
                  size="small"
                  disabled={!isFinished}
                  color="primary"
                  onClick={handleDownload}
                >
                  <DownloadIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
            <Tooltip title={t("common:delete")}>
              <span>
                <IconButton
                  size="small"
                  onClick={() => setDeleteDialogOpen(true)}
                  disabled={isRunning}
                  color="error"
                >
                  <DeleteIcon fontSize="small" />
                </IconButton>
              </span>
            </Tooltip>
          </Box>
        </Box>

        {/* Results */}
        {isFinished && (
          <Box sx={{ mt: 4 }}>
            <DatasetTable
              fetchPage={fetchPage}
              initialPageSize={5}
              datasetPath={prediction.results_path}
              columnTypes={columnTypes}
              showExportButton={false}
              baseBackgroundColor={theme.palette.background.paper}
              showBorder={false}
              targetColumn={targetColumn}
            />
          </Box>
        )}

        {/* Show loading indicator if prediction is running */}
        {isRunning && (
          <Box
            sx={{
              py: 4,
              textAlign: "center",
              color: "text.secondary",
            }}
          >
            <CircularProgress size={24} />
            <Typography variant="body2" sx={{ mt: 2 }}>
              {t("prediction:label.predictionInProgress")}
            </Typography>
          </Box>
        )}
      </Box>

      <DeleteConfirmationModal
        open={deleteDialogOpen}
        onClose={() => setDeleteDialogOpen(false)}
        onConfirm={handleDelete}
        content={t("prediction:label.confirmDeletion")}
      />
    </>
  );
}

PredictionCard.propTypes = {
  prediction: PropTypes.shape({
    id: PropTypes.number.isRequired,
    status: PropTypes.number.isRequired,
    created: PropTypes.string,
    dataset_id: PropTypes.number,
    dataset: PropTypes.shape({
      name: PropTypes.string,
    }),
    results_path: PropTypes.string,
  }).isRequired,
  onDelete: PropTypes.func,
  onUpdate: PropTypes.func,
  displayNumber: PropTypes.number,
};
