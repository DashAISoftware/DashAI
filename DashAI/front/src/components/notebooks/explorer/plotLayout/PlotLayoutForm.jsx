import React, { useState, useCallback, memo, useMemo } from "react";
import {
  Box,
  Typography,
  Divider,
  Stack,
  Button,
  Chip,
  alpha,
} from "@mui/material";
import { useTheme } from "@mui/material/styles";
import GeneralForm from "./forms/GeneralForm";
import TraceForm from "./forms/TraceForm";
import XAxisForm from "./forms/XAxisForm";
import YAxisForm from "./forms/YAxisForm";
import LegendForm from "./forms/LegendForm";
import DimensionsForm from "./forms/DimensionsForm";
import { useTranslation } from "react-i18next";

const PlotLayoutForm = memo(function PlotLayoutForm({
  data,
  setData,
  layout,
  setLayout,
  onSave,
  sx = {},
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const theme = useTheme();
  const [modified, setModified] = useState(false);
  const [localLayout, setLocalLayout] = useState(() => structuredClone(layout));
  const [localData, setLocalData] = useState(() => structuredClone(data));
  const [activeSection, setActiveSection] = useState("general");

  const hasDimensions = data?.[0]?.dimensions;
  const sections = useMemo(
    () => [
      { key: "general", label: t("datasets:label.generalSettings") },
      ...(Array.isArray(data)
        ? data.map((trace, i) => ({
            key: `trace-${i}`,
            label: t("datasets:label.traceIdx", {
              index: i + 1,
              trace: trace.name || trace.type,
            }),
          }))
        : []),
      ...(hasDimensions
        ? [{ key: "dimensions", label: t("datasets:label.dimensionsLabels") }]
        : [
            { key: "xaxis", label: t("datasets:label.xAxis") },
            { key: "yaxis", label: t("datasets:label.yAxis", "Y Axis") },
          ]),
      { key: "legend", label: t("datasets:label.legend", "Legend") },
    ],
    [data, t, hasDimensions],
  );

  // Ensure activeSection is valid when data changes
  const validSection = sections.find((s) => s.key === activeSection)
    ? activeSection
    : "general";

  if (!layout) return null;

  const handleTraceChange = useCallback(
    (index, path, value) => {
      const newData = [...data];
      const newTrace = structuredClone(newData[index]);
      const keys = path.split(".");
      let obj = newTrace;
      for (let i = 0; i < keys.length - 1; i++) {
        const k = keys[i];
        obj[k] = obj[k] || {};
        obj = obj[k];
      }
      obj[keys[keys.length - 1]] = value;
      newData[index] = newTrace;
      setData(newData);
      setModified(true);
    },
    [data, setData],
  );

  const handleChange = useCallback(
    (field, value) => {
      setLayout({ ...layout, [field]: value });
      setModified(true);
    },
    [layout, setLayout],
  );

  const handleCancel = useCallback(() => {
    setLayout(structuredClone(localLayout));
    setData(structuredClone(localData));
    setModified(false);
  }, [localLayout, localData, setLayout, setData]);

  const handleSave = useCallback(() => {
    setLocalData(structuredClone(data));
    setLocalLayout(structuredClone(layout));
    setModified(false);
    onSave();
  }, [data, layout, onSave]);

  const handleAxisChange = useCallback(
    (axis, field, value) => {
      setLayout({
        ...layout,
        [axis]: { ...layout[axis], [field]: value },
      });
      setModified(true);
    },
    [layout, setLayout],
  );

  const renderActiveTrace = () => {
    const idx = parseInt(validSection.split("-")[1], 10);
    const trace = Array.isArray(data) ? data[idx] : null;
    return trace ? (
      <TraceForm
        layout={layout}
        trace={trace}
        index={idx}
        handleTraceChange={handleTraceChange}
        handleChange={handleChange}
      />
    ) : null;
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        height: "100%",
        bgcolor: "background.paper",
        color: "text.primary",
        ...sx,
      }}
    >
      {/* Header */}
      <Box sx={{ px: 4, pt: 4, pb: 2, flexShrink: 0 }}>
        <Typography variant="sectionLabel" sx={{ color: "text.secondary" }}>
          {t("datasets:label.editPlotLayout")}
        </Typography>
      </Box>

      <Divider sx={{ borderColor: "ui.borderLight", flexShrink: 0 }} />

      {/* Pill tab bar */}
      <Box
        sx={{
          display: "flex",
          flexWrap: "wrap",
          gap: 3,
          p: 3,
          borderBottom: "1px solid",
          borderColor: "ui.borderLight",
          flexShrink: 0,
        }}
      >
        {sections.map((section) => {
          const isActive = validSection === section.key;
          return (
            <Chip
              key={section.key}
              label={section.label}
              size="small"
              onClick={() => setActiveSection(section.key)}
              sx={{
                fontFamily: '"IBM Plex Mono", monospace',
                fontSize: "0.65rem",
                letterSpacing: "0.08em",
                textTransform: "uppercase",
                height: 24,
                bgcolor: isActive
                  ? alpha(theme.palette.primary.main, 0.14)
                  : "transparent",
                color: isActive ? "primary.main" : "text.secondary",
                border: "1px solid",
                borderColor: isActive ? "primary.main" : "ui.borderLight",
                borderRadius: "10px",
                cursor: "pointer",
                "&:hover": {
                  bgcolor: isActive
                    ? alpha(theme.palette.primary.main, 0.2)
                    : alpha(theme.palette.primary.main, 0.04),
                  borderColor: "primary.light",
                },
              }}
            />
          );
        })}
      </Box>

      {/* Active section content */}
      <Box
        sx={{
          flex: 1,
          overflowY: "auto",
          p: 4,
          // Compact input boxes across every field in the form.
          "& .MuiInputBase-root": { minHeight: 34 },
          "& .MuiInputBase-input": {
            paddingTop: "4px",
            paddingBottom: "4px",
          },
          // Re center the resting (unshrunk) outlined label for the shorter box.
          "& .MuiInputLabel-outlined:not(.MuiInputLabel-shrink)": {
            transform: "translate(14px, 5px) scale(1)",
          },
        }}
      >
        {validSection === "general" && (
          <GeneralForm layout={layout} handleChange={handleChange} />
        )}
        {validSection.startsWith("trace-") && renderActiveTrace()}
        {validSection === "dimensions" && (
          <DimensionsForm data={data} handleTraceChange={handleTraceChange} />
        )}
        {validSection === "xaxis" && (
          <XAxisForm
            data={data}
            layout={layout}
            handleAxisChange={handleAxisChange}
            handleTraceChange={handleTraceChange}
          />
        )}
        {validSection === "yaxis" && (
          <YAxisForm
            data={data}
            layout={layout}
            handleAxisChange={handleAxisChange}
            handleTraceChange={handleTraceChange}
          />
        )}
        {validSection === "legend" && (
          <LegendForm layout={layout} handleChange={handleChange} />
        )}
      </Box>

      <Divider sx={{ borderColor: "ui.borderLight", flexShrink: 0 }} />

      {/* Save / Cancel footer */}
      <Stack
        direction="row"
        spacing={4}
        justifyContent="flex-end"
        sx={{ p: 3, flexShrink: 0 }}
      >
        <Button variant="outlined" onClick={handleCancel} disabled={!modified}>
          {t("common:cancel")}
        </Button>
        <Button
          variant="contained"
          color="primary"
          onClick={handleSave}
          disabled={!modified}
        >
          {t("common:save")}
        </Button>
      </Stack>
    </Box>
  );
});

export default PlotLayoutForm;
