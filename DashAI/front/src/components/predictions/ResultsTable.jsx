import React, { useEffect, useState, useCallback } from "react";
import {
  Box,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { getPredictionStatus } from "../../utils/predictionStatus";
import DatasetTable from "../notebooks/dataset/DatasetTable";
import {
  getDatasetFile,
  getDatasetFileFiltered,
  getDatasetTypesByFilePath,
} from "../../api/datasets";
import { useTranslation } from "react-i18next";
import {
  getTargetDecimals,
  formatPredictionRows,
} from "../../utils/predictionFormat";

const RUNNING_STATUSES = [1, 2]; // Delivered or Started

function ResultsTable({
  selectedPrediction,
  datasetSample = null,
  targetColumn = null,
}) {
  const theme = useTheme();
  const [loadingExecution, setLoadingExecution] = useState(
    RUNNING_STATUSES.includes(getPredictionStatus(selectedPrediction?.status)),
  );
  const [columnTypes, setColumnTypes] = useState({});
  const targetDecimals = React.useMemo(
    () => getTargetDecimals(datasetSample, targetColumn),
    [datasetSample, targetColumn],
  );
  const { t } = useTranslation(["prediction"]);

  useEffect(() => {
    if (!selectedPrediction?.results_path) return;
    getDatasetTypesByFilePath(selectedPrediction.results_path)
      .then(setColumnTypes)
      .catch(() => {});
  }, [selectedPrediction?.results_path]);

  const fetchPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      const hasFilters =
        filterModel?.items?.length > 0 || (sortModel && sortModel.length > 0);
      const data = hasFilters
        ? await getDatasetFileFiltered(
            selectedPrediction.results_path,
            page,
            pageSize,
            filterModel,
            sortModel,
          )
        : await getDatasetFile(selectedPrediction.results_path, page, pageSize);
      return {
        rows: formatPredictionRows(
          data.rows ?? [],
          targetColumn,
          targetDecimals,
        ),
        total: data.total ?? 0,
      };
    },
    [selectedPrediction, targetColumn, targetDecimals],
  );

  useEffect(() => {
    if (!selectedPrediction) return;
    setLoadingExecution(
      RUNNING_STATUSES.includes(
        getPredictionStatus(selectedPrediction?.status),
      ),
    );
  }, [selectedPrediction]);

  return (
    <Box>
      <Typography variant="subtitle1" fontWeight={600}>
        {t("prediction:label.predictionResults")}
      </Typography>

      <Typography
        variant="subtitle2"
        sx={{ color: theme.palette.text.secondary, mb: 2, display: "block" }}
      >
        {loadingExecution
          ? t("prediction:label.predictionStillRunningResults")
          : t("prediction:label.resultsPreviewDownloadInfo")}
      </Typography>

      {/* Show loading indicator if prediction is running */}
      {loadingExecution && (
        <Box
          sx={{
            py: 8,
            textAlign: "center",
            color: theme.palette.text.secondary,
          }}
        >
          <CircularProgress size={28} />
          <Typography variant="body2" sx={{ mt: 2 }}>
            {t("prediction:label.predictionStillRunning")}
          </Typography>
        </Box>
      )}

      {!loadingExecution &&
        selectedPrediction &&
        selectedPrediction?.status === 3 && ( // Finished
          <>
            <Typography
              variant="body2"
              sx={{ color: theme.palette.text.secondary, mb: 4 }}
            >
              {selectedPrediction.dataset
                ? t("prediction:label.basedOnDataset", {
                    datasetName: selectedPrediction.dataset.name,
                  })
                : t("prediction:label.manuallyProvidedInputData")}
            </Typography>
            <Paper>
              <DatasetTable
                fetchPage={fetchPage}
                initialPageSize={10}
                datasetPath={selectedPrediction.results_path}
                datasetName={
                  selectedPrediction.dataset?.name ?? "prediction_results"
                }
                columnTypes={columnTypes}
              />
            </Paper>
          </>
        )}
    </Box>
  );
}

export default ResultsTable;
