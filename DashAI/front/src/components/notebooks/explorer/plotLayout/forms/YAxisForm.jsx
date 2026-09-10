import React from "react";
import {
  Box,
  TextField,
  FormControlLabel,
  Switch,
  Divider,
  Typography,
  useTheme,
} from "@mui/material";

import DebouncedColorPicker from "../DebouncedColorPicker";
import { useTranslation } from "react-i18next";

const SectionLabel = ({ children }) => (
  <Typography
    variant="overline"
    color="text.secondary"
    sx={{ lineHeight: 1.5, display: "block" }}
  >
    {children}
  </Typography>
);

export default function YAxisForm({
  data,
  layout,
  handleAxisChange,
  handleTraceChange,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const tickvalsArray = Array.isArray(data[0]?.y) ? data[0].y : [];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {/* Title */}
      <SectionLabel>
        {t("datasets:label.axisTitle", { axis: "Y" })}
      </SectionLabel>

      <TextField
        label={t("datasets:label.axisTitle", { axis: "Y" })}
        variant="outlined"
        size="small"
        value={layout.yaxis?.title?.text || ""}
        onChange={(e) =>
          handleAxisChange("yaxis", "title", {
            ...layout.yaxis?.title,
            text: e.target.value,
          })
        }
        fullWidth
      />

      <TextField
        label={t("datasets:label.axisFontSize", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.title?.font?.size || 14}
        onChange={(e) =>
          handleAxisChange("yaxis", "title", {
            ...layout.yaxis?.title,
            font: {
              ...layout.yaxis?.title?.font,
              size: parseInt(e.target.value, 10) || 14,
            },
          })
        }
        fullWidth
        slotProps={{ htmlInput: { min: 8, max: 72 } }}
      />

      <DebouncedColorPicker
        label={t("datasets:label.axisTitleColor", { axis: "Y" })}
        value={layout.yaxis?.title?.font?.color || theme.palette.text.primary}
        onChange={(color) =>
          handleAxisChange("yaxis", "title", {
            ...layout.yaxis?.title,
            font: { ...layout.yaxis?.title?.font, color },
          })
        }
      />

      <TextField
        label={t("datasets:label.axisTitleStandoff", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.title?.standoff ?? 15}
        onChange={(e) =>
          handleAxisChange("yaxis", "title", {
            ...layout.yaxis?.title,
            standoff: parseInt(e.target.value, 10) || 0,
          })
        }
        fullWidth
        slotProps={{ htmlInput: { min: 0 } }}
      />

      <Divider />

      {/* Ticks */}
      <SectionLabel>{t("datasets:label.ticks", "Ticks")}</SectionLabel>

      <DebouncedColorPicker
        label={t("datasets:label.axisTickFontColor", { axis: "Y" })}
        value={layout.yaxis?.tickfont?.color || theme.palette.text.secondary}
        onChange={(color) =>
          handleAxisChange("yaxis", "tickfont", {
            ...layout.yaxis?.tickfont,
            color,
          })
        }
      />

      <TextField
        label={t("datasets:label.axisTickFontSize", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.tickfont?.size ?? 12}
        onChange={(e) =>
          handleAxisChange("yaxis", "tickfont", {
            ...layout.yaxis?.tickfont,
            size: parseInt(e.target.value, 10) || 12,
          })
        }
        fullWidth
        slotProps={{ htmlInput: { min: 8, max: 72 } }}
      />

      <TextField
        label={t("datasets:label.axisTickAngle", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.tickangle ?? 0}
        onChange={(e) =>
          handleAxisChange(
            "yaxis",
            "tickangle",
            parseInt(e.target.value, 10) || 0,
          )
        }
        fullWidth
        slotProps={{ htmlInput: { min: -360, max: 360 } }}
      />

      {tickvalsArray.length > 0 && (
        <TextField
          label={t("datasets:label.tickLabels", "Tick Labels")}
          variant="outlined"
          size="small"
          multiline
          minRows={3}
          maxRows={8}
          value={data[0].y.join("\n")}
          onChange={(e) => {
            handleTraceChange(0, "y", e.target.value.split("\n"));
          }}
          helperText={t(
            "datasets:label.tickLabelsHelper",
            "One label per line",
          )}
          fullWidth
        />
      )}

      <Divider />

      {/* Grid */}
      <SectionLabel>{t("datasets:label.grid", "Grid")}</SectionLabel>

      <FormControlLabel
        control={
          <Switch
            checked={layout.yaxis?.showgrid ?? true}
            onChange={(e) =>
              handleAxisChange("yaxis", "showgrid", e.target.checked)
            }
            color="primary"
          />
        }
        label={t("datasets:label.showGrid", { axis: "Y" })}
      />

      <DebouncedColorPicker
        label={t("datasets:label.axisGridColor", { axis: "Y" })}
        value={layout.yaxis?.gridcolor || theme.palette.ui.divider}
        onChange={(color) => handleAxisChange("yaxis", "gridcolor", color)}
      />

      <TextField
        label={t("datasets:label.axisGridWidth", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.gridwidth ?? 1}
        onChange={(e) =>
          handleAxisChange(
            "yaxis",
            "gridwidth",
            parseInt(e.target.value, 10) || 1,
          )
        }
        fullWidth
        slotProps={{ htmlInput: { min: 1, max: 10 } }}
      />

      <FormControlLabel
        control={
          <Switch
            checked={layout.yaxis?.zeroline ?? true}
            onChange={(e) =>
              handleAxisChange("yaxis", "zeroline", e.target.checked)
            }
            color="primary"
          />
        }
        label={t("datasets:label.showZeroLine", { axis: "Y" })}
      />

      <Divider />

      {/* Line */}
      <SectionLabel>{t("datasets:label.axisLine", "Axis Line")}</SectionLabel>

      <DebouncedColorPicker
        label={t("datasets:label.axisLineColor", { axis: "Y" })}
        value={layout.yaxis?.linecolor || theme.palette.text.primary}
        onChange={(color) => handleAxisChange("yaxis", "linecolor", color)}
      />

      <TextField
        label={t("datasets:label.axisLineWidth", { axis: "Y" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.yaxis?.linewidth ?? 1}
        onChange={(e) =>
          handleAxisChange(
            "yaxis",
            "linewidth",
            parseInt(e.target.value, 10) || 1,
          )
        }
        fullWidth
        slotProps={{ htmlInput: { min: 1, max: 10 } }}
      />
    </Box>
  );
}
