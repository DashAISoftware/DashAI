import React from "react";
import { Box, MenuItem, TextField, Divider, Typography } from "@mui/material";

import DebouncedColorPicker from "../DebouncedColorPicker";
import { useTranslation } from "react-i18next";

const FONT_LIST = [
  "Arial",
  "Balto",
  "Courier New",
  "Droid Sans",
  "Droid Serif",
  "Droid Sans Mono",
  "Gravitas One",
  "Old Standard TT",
  "Open Sans",
  "PT Sans Narrow",
  "Raleway",
  "Times New Roman",
];

const SectionLabel = ({ children }) => (
  <Typography
    variant="overline"
    color="text.secondary"
    sx={{ lineHeight: 1.5, display: "block" }}
  >
    {children}
  </Typography>
);

export default function GeneralForm({ layout, handleChange }) {
  const { t } = useTranslation(["datasets"]);

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 5 }}>
      {/* Title */}
      <SectionLabel>{t("datasets:label.title", "Title")}</SectionLabel>

      <TextField
        label={t("datasets:label.title")}
        variant="outlined"
        size="small"
        value={layout.title?.text || ""}
        onChange={(e) =>
          handleChange("title", { ...layout.title, text: e.target.value })
        }
        fullWidth
      />

      <Box sx={{ display: "flex", gap: 4 }}>
        <TextField
          label={t("datasets:label.titleFontSize")}
          variant="outlined"
          size="small"
          type="number"
          value={layout.title?.font?.size || 16}
          onChange={(e) =>
            handleChange("title", {
              ...layout.title,
              font: {
                ...layout.title?.font,
                size: parseInt(e.target.value, 10) || 16,
              },
            })
          }
          fullWidth
          slotProps={{ htmlInput: { min: 8, max: 72 } }}
        />

        <TextField
          select
          label={t("datasets:label.fontFamily")}
          variant="outlined"
          size="small"
          value={layout.font?.family || "Arial"}
          onChange={(e) =>
            handleChange("font", { ...layout.font, family: e.target.value })
          }
          fullWidth
        >
          {FONT_LIST.map((font) => (
            <MenuItem key={font} value={font}>
              {font}
            </MenuItem>
          ))}
        </TextField>
      </Box>

      <DebouncedColorPicker
        label={t("datasets:label.titleColor")}
        value={layout.title?.font?.color || "#2A3F5F"}
        onChange={(color) =>
          handleChange("title", {
            ...layout.title,
            font: { ...layout.title?.font, color },
          })
        }
      />

      <Divider />

      {/* Colors */}
      <SectionLabel>{t("datasets:label.colors")}</SectionLabel>

      <DebouncedColorPicker
        label={t("datasets:label.backgroundColor")}
        value={layout.paper_bgcolor || "#ffffff"}
        onChange={(color) => handleChange("paper_bgcolor", color)}
      />

      <DebouncedColorPicker
        label={t("datasets:label.plotBackgroundColor")}
        value={layout.plot_bgcolor || "#E5ECF6"}
        onChange={(color) => handleChange("plot_bgcolor", color)}
      />

      <Divider />

      {/* Margins */}
      <SectionLabel>{t("datasets:label.margins")}</SectionLabel>

      <Box sx={{ display: "flex", gap: 4 }}>
        <TextField
          label={t("datasets:label.marginLeft")}
          variant="outlined"
          size="small"
          type="number"
          value={layout.margin?.l ?? 80}
          onChange={(e) =>
            handleChange("margin", {
              ...layout.margin,
              l: parseInt(e.target.value, 10) || 0,
            })
          }
          fullWidth
          slotProps={{ htmlInput: { min: 0 } }}
        />
        <TextField
          label={t("datasets:label.marginRight")}
          variant="outlined"
          size="small"
          type="number"
          value={layout.margin?.r ?? 80}
          onChange={(e) =>
            handleChange("margin", {
              ...layout.margin,
              r: parseInt(e.target.value, 10) || 0,
            })
          }
          fullWidth
          slotProps={{ htmlInput: { min: 0 } }}
        />
      </Box>

      <Box sx={{ display: "flex", gap: 4 }}>
        <TextField
          label={t("datasets:label.marginTop")}
          variant="outlined"
          size="small"
          type="number"
          value={layout.margin?.t ?? 100}
          onChange={(e) =>
            handleChange("margin", {
              ...layout.margin,
              t: parseInt(e.target.value, 10) || 0,
            })
          }
          fullWidth
          slotProps={{ htmlInput: { min: 0 } }}
        />
        <TextField
          label={t("datasets:label.marginBottom")}
          variant="outlined"
          size="small"
          type="number"
          value={layout.margin?.b ?? 80}
          onChange={(e) =>
            handleChange("margin", {
              ...layout.margin,
              b: parseInt(e.target.value, 10) || 0,
            })
          }
          fullWidth
          slotProps={{ htmlInput: { min: 0 } }}
        />
      </Box>
    </Box>
  );
}
