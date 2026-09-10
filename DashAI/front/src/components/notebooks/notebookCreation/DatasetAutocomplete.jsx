import React from "react";
import { Box, Typography, Autocomplete, TextField, Chip } from "@mui/material";
import { formatDate } from "../../../pages/results/constants/formatDate";
import { useTranslation } from "react-i18next";

const TASK_KEY_MAP = {
  "Tabular Classification": "tabularClassification",
  "Image Classification": "imageClassification",
  "Text Classification": "textClassification",
  Translation: "translation",
  Regression: "regression",
  EDA: "eda",
};

export default function DatasetAutocomplete({
  datasets,
  selectedDataset,
  setSelectedDataset,
  showDetails = true,
}) {
  const { t } = useTranslation(["datasets", "common"]);

  const TASK_TRANSLATIONS = {
    tabularClassification: () => t("datasets:task.tabularClassification"),
    imageClassification: () => t("datasets:task.imageClassification"),
    textClassification: () => t("datasets:task.textClassification"),
    translation: () => t("datasets:task.translation"),
    regression: () => t("datasets:task.regression"),
    eda: () => t("datasets:task.eda"),
  };

  const getTaskLabel = (dataset) => {
    if (!dataset?.task) return null;
    const key = TASK_KEY_MAP[dataset.task];
    return TASK_TRANSLATIONS[key] ? TASK_TRANSLATIONS[key]() : dataset.task;
  };

  return (
    <Box width="100%">
      <Box sx={{ width: "100%", mx: "auto" }}>
        <Autocomplete
          data-tour="models-dataset-selection"
          options={datasets}
          getOptionLabel={(option) => option.name}
          isOptionEqualToValue={(opt, val) => opt.id === val.id}
          value={selectedDataset}
          onChange={(event, newValue) => {
            setSelectedDataset(newValue);
          }}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t("datasets:label.selectDataset")}
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
                    gap: 1,
                  }}
                >
                  <Typography variant="body1" fontWeight="medium">
                    {option.name}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {getTaskLabel(option)
                      ? getTaskLabel(option)
                      : `${t("common:created")}: ${formatDate(option.created)}`}
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
          sx={{ mb: 6 }}
        />

        {showDetails && selectedDataset && (
          <Box
            sx={{
              mt: 6,
              p: 6,
              border: 1,
              borderColor: "divider",
              borderRadius: 2,
            }}
          >
            <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  {t("common:name")}:
                </Typography>
                <Chip label={selectedDataset.name} size="small" />
              </Box>
              <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
                <Typography variant="body2" fontWeight="medium">
                  {getTaskLabel(selectedDataset)
                    ? t("datasets:label.task", "Task")
                    : t("common:created")}
                  :
                </Typography>
                <Typography variant="body2">
                  {getTaskLabel(selectedDataset) ??
                    formatDate(selectedDataset.created)}
                </Typography>
              </Box>
              {/* Single line for Rows | Columns */}
              <Typography variant="body2" fontWeight="medium">
                {t("datasets:label.rowsColumnsInfo", {
                  totalRows: selectedDataset.total_rows ?? "...",
                  totalColumns: selectedDataset.total_columns ?? "...",
                })}
              </Typography>
            </Box>
          </Box>
        )}
      </Box>
    </Box>
  );
}
