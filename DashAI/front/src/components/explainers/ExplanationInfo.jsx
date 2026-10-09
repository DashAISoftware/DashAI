import React from "react";
import PropTypes from "prop-types";
import { Box, Chip, Stack, Typography } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useTranslation } from "react-i18next";

/**
 * Read only summary of the model's input and target columns, shown while
 * choosing the data to explain so the user knows which features feed the model.
 */
export default function ExplanationInfo({ inputColumns, outputColumns }) {
  const { t } = useTranslation(["explainers"]);

  if (
    (!inputColumns || inputColumns.length === 0) &&
    (!outputColumns || outputColumns.length === 0)
  ) {
    return null;
  }

  return (
    <Box
      sx={{
        p: 4,
        borderRadius: 2,
        border: 1,
        borderColor: "primary.main",
        bgcolor: (theme) => `${theme.palette.primary.main}14`,
      }}
    >
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
        <InfoOutlinedIcon color="primary" fontSize="small" />
        <Typography variant="subtitle2" color="primary">
          {t("explainers:label.explanationInfo")}
        </Typography>
      </Stack>

      <Typography variant="caption" fontWeight={600} display="block">
        {t("explainers:label.inputColumns")}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1, mb: 3 }}>
        {(inputColumns ?? []).map((col) => (
          <Chip key={col} label={col} size="small" variant="outlined" />
        ))}
      </Box>

      <Typography variant="caption" fontWeight={600} display="block">
        {t("explainers:label.targetColumn")}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}>
        {(outputColumns ?? []).map((col) => (
          <Chip key={col} label={col} size="small" color="primary" />
        ))}
      </Box>
    </Box>
  );
}

ExplanationInfo.propTypes = {
  inputColumns: PropTypes.arrayOf(PropTypes.string),
  outputColumns: PropTypes.arrayOf(PropTypes.string),
};
