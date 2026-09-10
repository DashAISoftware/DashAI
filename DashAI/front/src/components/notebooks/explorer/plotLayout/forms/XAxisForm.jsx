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

export default function XAxisForm({
  data,
  layout,
  handleAxisChange,
  handleTraceChange,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();
  const tickvalsArray = Array.isArray(data[0]?.x) ? data[0].x : [];

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {/* Title */}
      <SectionLabel>
        {t("datasets:label.axisTitle", { axis: "X" })}
      </SectionLabel>

      <TextField
        label={t("datasets:label.axisTitle", { axis: "X" })}
        variant="outlined"
        size="small"
        value={layout.xaxis?.title?.text || ""}
        onChange={(e) =>
          handleAxisChange("xaxis", "title", {
            ...layout.xaxis?.title,
            text: e.target.value,
          })
        }
        fullWidth
      />

      <TextField
        label={t("datasets:label.axisFontSize", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.title?.font?.size || 14}
        onChange={(e) =>
          handleAxisChange("xaxis", "title", {
            ...layout.xaxis?.title,
            font: {
              ...layout.xaxis?.title?.font,
              size: parseInt(e.target.value, 10) || 14,
            },
          })
        }
        fullWidth
        slotProps={{ htmlInput: { min: 8, max: 72 } }}
      />

      <DebouncedColorPicker
        label={t("datasets:label.axisTitleColor", { axis: "X" })}
        value={layout.xaxis?.title?.font?.color || theme.palette.text.primary}
        onChange={(color) =>
          handleAxisChange("xaxis", "title", {
            ...layout.xaxis?.title,
            font: { ...layout.xaxis?.title?.font, color },
          })
        }
      />

      <TextField
        label={t("datasets:label.axisTitleStandoff", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.title?.standoff ?? 15}
        onChange={(e) =>
          handleAxisChange("xaxis", "title", {
            ...layout.xaxis?.title,
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
        label={t("datasets:label.axisTickFontColor", { axis: "X" })}
        value={layout.xaxis?.tickfont?.color || theme.palette.text.secondary}
        onChange={(color) =>
          handleAxisChange("xaxis", "tickfont", {
            ...layout.xaxis?.tickfont,
            color,
          })
        }
      />

      <TextField
        label={t("datasets:label.axisTickFontSize", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.tickfont?.size ?? 12}
        onChange={(e) =>
          handleAxisChange("xaxis", "tickfont", {
            ...layout.xaxis?.tickfont,
            size: parseInt(e.target.value, 10) || 12,
          })
        }
        fullWidth
        slotProps={{ htmlInput: { min: 8, max: 72 } }}
      />

      <TextField
        label={t("datasets:label.axisTickAngle", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.tickangle ?? 0}
        onChange={(e) =>
          handleAxisChange(
            "xaxis",
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
          value={data[0].x.join("\n")}
          onChange={(e) => {
            handleTraceChange(0, "x", e.target.value.split("\n"));
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
            checked={layout.xaxis?.showgrid ?? true}
            onChange={(e) =>
              handleAxisChange("xaxis", "showgrid", e.target.checked)
            }
            color="primary"
          />
        }
        label={t("datasets:label.showGrid", { axis: "X" })}
      />

      <DebouncedColorPicker
        label={t("datasets:label.axisGridColor", { axis: "X" })}
        value={layout.xaxis?.gridcolor || theme.palette.ui.divider}
        onChange={(color) => handleAxisChange("xaxis", "gridcolor", color)}
      />

      <TextField
        label={t("datasets:label.axisGridWidth", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.gridwidth ?? 1}
        onChange={(e) =>
          handleAxisChange(
            "xaxis",
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
            checked={layout.xaxis?.zeroline ?? true}
            onChange={(e) =>
              handleAxisChange("xaxis", "zeroline", e.target.checked)
            }
            color="primary"
          />
        }
        label={t("datasets:label.showZeroLine", { axis: "X" })}
      />

      <Divider />

      {/* Line */}
      <SectionLabel>{t("datasets:label.axisLine", "Axis Line")}</SectionLabel>

      <DebouncedColorPicker
        label={t("datasets:label.axisLineColor", { axis: "X" })}
        value={layout.xaxis?.linecolor || theme.palette.text.primary}
        onChange={(color) => handleAxisChange("xaxis", "linecolor", color)}
      />

      <TextField
        label={t("datasets:label.axisLineWidth", { axis: "X" })}
        variant="outlined"
        size="small"
        type="number"
        value={layout.xaxis?.linewidth ?? 1}
        onChange={(e) =>
          handleAxisChange(
            "xaxis",
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
