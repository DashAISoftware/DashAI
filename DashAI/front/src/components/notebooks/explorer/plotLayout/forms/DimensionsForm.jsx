import React from "react";
import { TextField, Box, Typography, useTheme } from "@mui/material";
import { useTranslation } from "react-i18next";

export default function DimensionsForm({ data, handleTraceChange }) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 5 }}>
      {data[0].dimensions.map((dim, idx) => (
        <Box
          key={idx}
          sx={{
            p: 4,
            border: `1px solid ${
              theme.palette.ui.borderLight || theme.palette.divider
            }`,
            borderRadius: 1,
            bgcolor: theme.palette.background.default,
          }}
        >
          <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 4 }}>
            {t("datasets:label.dimensionIdx", {
              idx: idx + 1,
              label: dim.label || `Dimension ${idx + 1}`,
            })}
          </Typography>

          <TextField
            label={t("datasets:label.dimensionTitle")}
            variant="outlined"
            size="small"
            value={dim.label || ""}
            onChange={(e) =>
              handleTraceChange(0, `dimensions.${idx}.label`, e.target.value)
            }
            fullWidth
          />
        </Box>
      ))}
    </Box>
  );
}
