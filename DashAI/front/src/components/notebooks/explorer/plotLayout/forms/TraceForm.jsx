import React from "react";
import { Box, TextField } from "@mui/material";

import DebouncedColorPicker from "../DebouncedColorPicker";
import ColorscaleSelector from "../ColorscaleSelector";
import { useTranslation } from "react-i18next";

const usesColormap = (trace) =>
  ["heatmap", "surface", "scatter3d", "choropleth", "histogram2d"].includes(
    trace.type,
  );

export default function TraceForm({
  layout,
  trace,
  index,
  handleTraceChange,
  handleChange,
}) {
  const { t } = useTranslation(["datasets", "common"]);

  // Pick a sensible fallback color when the trace has none set. The colorway
  // may be absent (e.g. backend explainer figures without a template), so guard
  // every access instead of assuming layout.template.layout.colorway exists.
  const colorway = layout?.template?.layout?.colorway;
  const fallbackColor = (i) =>
    (Array.isArray(colorway) && colorway[i % colorway.length]) || "#1f77b4";

  // Colors live in different fields per trace type: waterfall keeps them under
  // increasing/decreasing/totals.marker.color, line-mode scatters under
  // line.color, everything else under marker.color.
  const type = trace.type || "scatter";
  const isScatter = type === "scatter" || type === "scattergl";
  const mode = trace.mode || "";
  const showLine = isScatter && (mode === "" || mode.includes("lines"));
  const showMarker = !isScatter || mode === "" || mode.includes("markers");

  // px.imshow() (correlation matrix, density heatmap) sets coloraxis: "coloraxis"
  // on the trace, so its colorscale and colorbar live under layout.coloraxis and
  // the trace's own fields are ignored. A figure built straight from go.Heatmap
  // (the confusion matrix report) references no shared axis and reads both off
  // the trace instead, so every write below has to follow the same rule or it
  // lands on a key nothing renders from.
  const usesSharedColorAxis = Boolean(trace.coloraxis);
  const colorbarSrc = usesSharedColorAxis
    ? layout.coloraxis?.colorbar
    : trace.colorbar;
  const colorscaleSrc = usesSharedColorAxis
    ? layout.coloraxis?.colorscale
    : trace.colorscale;
  const reversescaleSrc = usesSharedColorAxis
    ? layout.coloraxis?.reversescale
    : trace.reversescale;

  const setColorscale = (newScale) => {
    if (usesSharedColorAxis) {
      handleChange("coloraxis", {
        ...layout.coloraxis,
        colorscale: newScale,
      });
    } else {
      handleTraceChange(index, "colorscale", newScale);
    }
  };

  // Plotly reverses a scale with a flag rather than by rewriting its stops, so
  // this works for a named preset and a hand built array alike.
  const setReversescale = (isReversed) => {
    if (usesSharedColorAxis) {
      handleChange("coloraxis", {
        ...layout.coloraxis,
        reversescale: isReversed,
      });
    } else {
      handleTraceChange(index, "reversescale", isReversed);
    }
  };

  const setColorbarField = (field, value) => {
    if (usesSharedColorAxis) {
      handleChange("coloraxis", {
        ...layout.coloraxis,
        colorbar: { ...layout.coloraxis?.colorbar, [field]: value },
      });
    } else {
      handleTraceChange(index, `colorbar.${field}`, value);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 4 }}>
      {/* Common trace settings */}
      <TextField
        label={t("common:name")}
        variant="outlined"
        size="small"
        value={trace.name || ""}
        onChange={(e) => handleTraceChange(index, "name", e.target.value)}
        fullWidth
      />

      {/* --- Waterfall Options (e.g. SHAP force plots): two/three colors --- */}
      {type === "waterfall" && (
        <>
          <DebouncedColorPicker
            label={t("datasets:label.increasingColor", "Increasing color")}
            value={trace.increasing?.marker?.color || "rgb(231,63,116)"}
            onChange={(color) =>
              handleTraceChange(index, "increasing.marker.color", color)
            }
          />
          <DebouncedColorPicker
            label={t("datasets:label.decreasingColor", "Decreasing color")}
            value={trace.decreasing?.marker?.color || "rgb(47,138,196)"}
            onChange={(color) =>
              handleTraceChange(index, "decreasing.marker.color", color)
            }
          />
          <DebouncedColorPicker
            label={t("datasets:label.totalsColor", "Totals color")}
            value={trace.totals?.marker?.color || "#4C78A8"}
            onChange={(color) =>
              handleTraceChange(index, "totals.marker.color", color)
            }
          />
        </>
      )}

      {/* --- Line / Marker Options --- */}
      {type !== "waterfall" && !usesColormap(trace) && (
        <>
          {showLine && (
            <DebouncedColorPicker
              label={t("datasets:label.lineColor", "Line color")}
              value={trace.line?.color || fallbackColor(index)}
              onChange={(color) =>
                handleTraceChange(index, "line.color", color)
              }
            />
          )}
          {showMarker && (
            <DebouncedColorPicker
              label={t("datasets:label.markerColor")}
              value={
                (typeof trace.marker?.color === "string" &&
                  trace.marker.color) ||
                fallbackColor(index)
              }
              onChange={(color) =>
                handleTraceChange(index, "marker.color", color)
              }
            />
          )}
        </>
      )}

      {/* --- Heatmap Options --- */}
      {usesColormap(trace) && (
        <>
          <ColorscaleSelector
            value={colorscaleSrc}
            onChange={setColorscale}
            reversed={reversescaleSrc}
            onReversedChange={setReversescale}
          />

          <DebouncedColorPicker
            label={t("datasets:label.colorbarBorderColor")}
            value={colorbarSrc?.bordercolor || "#FFFFFF"}
            onChange={(color) => setColorbarField("bordercolor", color)}
          />
          <TextField
            label={t("datasets:label.colorbarBorderWidth")}
            variant="outlined"
            size="small"
            type="number"
            value={colorbarSrc?.borderwidth || 0}
            onChange={(e) =>
              setColorbarField("borderwidth", parseInt(e.target.value, 10) || 0)
            }
            fullWidth
          />

          <DebouncedColorPicker
            label={t("datasets:label.colorbarTickFontColor")}
            value={colorbarSrc?.tickfont?.color || "#444444"}
            onChange={(color) =>
              setColorbarField("tickfont", {
                ...colorbarSrc?.tickfont,
                color,
              })
            }
          />
          <TextField
            label={t("datasets:label.colorbarTickFontSize")}
            variant="outlined"
            size="small"
            type="number"
            value={colorbarSrc?.tickfont?.size ?? 12}
            onChange={(e) =>
              setColorbarField("tickfont", {
                ...colorbarSrc?.tickfont,
                size: parseInt(e.target.value, 10) || 12,
              })
            }
            fullWidth
            slotProps={{ htmlInput: { min: 8, max: 72 } }}
          />
        </>
      )}
    </Box>
  );
}
