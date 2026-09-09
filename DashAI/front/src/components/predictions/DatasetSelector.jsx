import React, { useCallback, useEffect, useState } from "react";
import {
  Box,
  Typography,
  Autocomplete,
  TextField,
  Paper,
  Alert,
  Chip,
  FormControl,
  FormControlLabel,
  Radio,
  RadioGroup,
} from "@mui/material";
import DatasetTable from "../notebooks/dataset/DatasetTable";
import {
  getDatasetFile,
  getDatasetFileFiltered,
  getDatasetTypesByFilePath,
} from "../../api/datasets";
import { getPredictionSplits } from "../../api/predict";
import { formatDate } from "../../pages/results/constants/formatDate";
import { useTranslation } from "react-i18next";

function DatasetSelector({
  experiment,
  datasets,
  selectedDataset,
  setSelectedDataset,
  actionSlot = null,
  runId = null,
  onSplitChange = null,
}) {
  const { t } = useTranslation(["prediction", "common", "datasets"]);
  const [columnTypes, setColumnTypes] = useState({});
  const [splits, setSplits] = useState([]);
  const [trainingDatasetId, setTrainingDatasetId] = useState(null);
  const [split, setSplit] = useState("all");

  useEffect(() => {
    if (!selectedDataset?.file_path) return;
    getDatasetTypesByFilePath(selectedDataset.file_path)
      .then(setColumnTypes)
      .catch(() => {});
  }, [selectedDataset?.file_path]);

  useEffect(() => {
    if (!runId) return undefined;
    let cancelled = false;
    getPredictionSplits(runId)
      .then(({ splits: runSplits, trainingDatasetId: datasetId }) => {
        if (cancelled) return;
        setSplits(runSplits);
        setTrainingDatasetId(datasetId);
        if (!runSplits.some(({ name }) => name === "all")) {
          setSplit(runSplits[0]?.name ?? "all");
        }
      })
      .catch((error) => {
        console.error("Error fetching prediction splits", error);
      });
    return () => {
      cancelled = true;
    };
  }, [runId]);

  const isTrainingDataset =
    selectedDataset != null &&
    trainingDatasetId != null &&
    selectedDataset.id === trainingDatasetId;
  const showSplitSelector = isTrainingDataset && splits.length > 0;
  const offersWholeDataset = splits.some(({ name }) => name === "all");
  const effectiveSplit = showSplitSelector ? split : "all";
  const rowsInSplit = splits.find((s) => s.name === effectiveSplit)?.rows;

  useEffect(() => {
    onSplitChange?.(effectiveSplit);
  }, [effectiveSplit, onSplitChange]);

  const fetchDatasetPage = useCallback(
    async (page, pageSize, filterModel, sortModel) => {
      const hasFilters =
        filterModel?.items?.length > 0 || (sortModel && sortModel.length > 0);
      const data = hasFilters
        ? await getDatasetFileFiltered(
            selectedDataset.file_path,
            page,
            pageSize,
            filterModel,
            sortModel,
          )
        : await getDatasetFile(selectedDataset.file_path, page, pageSize);
      return { rows: data.rows ?? [], total: data.total ?? 0 };
    },
    [selectedDataset],
  );

  return (
    <Box sx={{ mb: 6 }}>
      <Box sx={{ display: "flex", alignItems: "stretch", gap: 2 }}>
        <Autocomplete
          sx={{ flex: 1 }}
          options={datasets}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(opt, val) => opt.id === val.id}
          value={selectedDataset}
          onChange={(_, newValue) => setSelectedDataset(newValue)}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t("prediction:label.selectDataset")}
              variant="outlined"
              placeholder={t("datasets:label.typeToSearchDatasets")}
            />
          )}
          renderOption={(props, option) => {
            const { key, ...rootProps } = props;
            return (
              <Box component="li" key={key} {...rootProps}>
                <Box
                  sx={{
                    display: "flex",
                    flexDirection: "column",
                    width: "100%",
                    gap: 0.25,
                  }}
                >
                  <Typography variant="body1" fontWeight="medium">
                    {option.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {t("common:created")}: {formatDate(option.created)}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {t("datasets:label.rowsColumnsInfo", {
                      totalRows: option.total_rows ?? "...",
                      totalColumns: option.total_columns ?? "...",
                    })}
                  </Typography>
                </Box>
              </Box>
            );
          }}
        />
        {actionSlot}
      </Box>
      {showSplitSelector && (
        <FormControl component="fieldset" sx={{ width: "100%", mt: 4 }}>
          <Typography gutterBottom>
            {t("prediction:label.datasetSplit")}
          </Typography>
          <Typography variant="caption" color="text.secondary">
            {offersWholeDataset
              ? t("prediction:label.datasetSplitDescription")
              : t("prediction:label.datasetSplitForwardOnly")}
          </Typography>
          <RadioGroup
            row
            value={split}
            onChange={(e) => setSplit(e.target.value)}
            sx={{ mt: 2 }}
          >
            {splits.map(({ name }) => (
              <FormControlLabel
                key={name}
                value={name}
                control={<Radio />}
                label={t(`common:${name === "val" ? "validation" : name}`, {
                  defaultValue: name,
                })}
              />
            ))}
          </RadioGroup>
          {rowsInSplit != null && (
            <Typography variant="caption" color="text.secondary">
              {t("prediction:label.rowsToPredict", { count: rowsInSplit })}
            </Typography>
          )}
        </FormControl>
      )}
      {selectedDataset && (
        <>
          <Alert severity="info" sx={{ mt: 4 }}>
            <Typography variant="h5" sx={{ mb: 2 }}>
              {t("prediction:label.predictionInfo")}
            </Typography>

            <Box sx={{ mb: 2 }}>
              <strong>{t("prediction:label.inputColumns")}:</strong>
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 1 }}>
                {experiment.input_columns.map((col) => (
                  <Chip
                    key={col}
                    label={col}
                    size="small"
                    variant="outlined"
                    sx={{ fontSize: "0.75rem" }}
                  />
                ))}
              </Box>
            </Box>

            <Box sx={{ display: "flex", alignItems: "center" }}>
              <strong>{t("prediction:label.targetColumn")}:</strong>
              <Chip
                label={experiment.output_columns[0]}
                size="small"
                color="primary"
                sx={{ ml: 2, fontSize: "0.75rem" }}
              />
            </Box>
          </Alert>

          <Paper>
            <DatasetTable
              fetchPage={fetchDatasetPage}
              initialPageSize={5}
              datasetPath={selectedDataset.file_path}
              columnTypes={columnTypes}
              showExportButton={false}
            />
          </Paper>
        </>
      )}
    </Box>
  );
}

export default DatasetSelector;
