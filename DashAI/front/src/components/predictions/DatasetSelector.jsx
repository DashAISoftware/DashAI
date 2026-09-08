import React, { useCallback, useEffect, useState } from "react";
import {
  Box,
  Typography,
  Autocomplete,
  TextField,
  Paper,
  Alert,
  Chip,
} from "@mui/material";
import DatasetTable from "../notebooks/dataset/DatasetTable";
import {
  getDataset,
  getDatasetFile,
  getDatasetFileFiltered,
  getDatasetTypesByFilePath,
} from "../../api/datasets";
import { formatDate } from "../../pages/results/constants/formatDate";
import { atomColumnNames, formatColumnAtom } from "../../utils/columnAtoms";
import { useTranslation } from "react-i18next";

function DatasetSelector({
  experiment,
  datasets,
  selectedDataset,
  setSelectedDataset,
  actionSlot = null,
}) {
  const { t } = useTranslation(["prediction", "common", "datasets"]);
  const [columnTypes, setColumnTypes] = useState({});
  const [rawInputColumns, setRawInputColumns] = useState([]);

  useEffect(() => {
    if (!selectedDataset?.file_path) return;
    getDatasetTypesByFilePath(selectedDataset.file_path)
      .then(setColumnTypes)
      .catch(() => {});
  }, [selectedDataset?.file_path]);

  // Not `experiment.input_columns`: a converter that adds or renames input
  // columns (e.g. BagOfWords' `bow_<word>`) means those names only exist
  // *inside* the session's own preprocessed data, never in a raw dataset.
  // Not the *selected* dataset's own columns either — a dataset can pass
  // `filter_datasets` by having extra columns beyond what's needed (e.g.
  // one already carrying pre-computed `bow_<word>` columns of its own),
  // and showing every one of those here made a single required column
  // ("text") look like hundreds. The session's own raw *training* dataset
  // (`experiment.dataset_id`) is the actual source of truth for what's
  // required — independent of whichever dataset happens to be selected.
  useEffect(() => {
    let cancelled = false;
    getDataset(experiment.dataset_id)
      .then((trainedDataset) =>
        getDatasetTypesByFilePath(`${trainedDataset.file_path}/dataset`),
      )
      .then((trainedTypes) => {
        if (cancelled) return;
        // `experiment.output_columns` holds column *atoms*
        // (`{kind: "column", name}` / `{kind: "group", converter_id, slot}`),
        // never plain names, so a raw `.includes(col)` against a raw column
        // name never matched and the target column leaked into this list.
        // Only `column` atoms have a real raw name to exclude here; a
        // `group` atom's real columns don't exist in the raw dataset at all
        // (and a group atom is rejected as a session target anyway), so it
        // correctly excludes nothing.
        const targetColumnNames = atomColumnNames(experiment.output_columns);
        setRawInputColumns(
          Object.keys(trainedTypes).filter(
            (col) => !targetColumnNames.includes(col),
          ),
        );
      })
      .catch(() => {
        if (!cancelled) setRawInputColumns([]);
      });
    return () => {
      cancelled = true;
    };
  }, [experiment.dataset_id, experiment.output_columns]);

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
      {selectedDataset && (
        <>
          <Alert severity="info" sx={{ mt: 4 }}>
            <Typography variant="h5" sx={{ mb: 2 }}>
              {t("prediction:label.predictionInfo")}
            </Typography>

            <Box sx={{ mb: 2 }}>
              <strong>{t("prediction:label.inputColumns")}:</strong>
              <Box sx={{ display: "flex", gap: 2, flexWrap: "wrap", mt: 1 }}>
                {rawInputColumns.map((col) => (
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
                label={formatColumnAtom(experiment.output_columns?.[0], {
                  converters: experiment.converters,
                  unknownLabel: t("common:unknown"),
                })}
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
