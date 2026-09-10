import React, { useRef, useState, useEffect } from "react";
import { Box, TextField, Checkbox, FormControlLabel } from "@mui/material";
import { useTranslation } from "react-i18next";

const TRANSPARENT = "rgba(0,0,0,0)";

// Any fully transparent CSS color (transparent keyword or an rgba/hsla with a
// zero alpha) counts as "transparent" for the toggle.
const isTransparentColor = (color) =>
  typeof color === "string" &&
  (color === "transparent" ||
    /^rgba?\(\s*[\d.]+\s*,\s*[\d.]+\s*,\s*[\d.]+\s*,\s*0(\.0+)?\s*\)$/.test(
      color,
    ));

export default function DebouncedColorPicker({
  label,
  value,
  onChange,
  delay = 300,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const [localValue, setLocalValue] = useState(value || "#000000");
  const timeoutRef = useRef(null);
  const transparent = isTransparentColor(value);
  // Remember the last non-transparent color so unchecking "Transparent"
  // restores it instead of falling back to black.
  const lastColorRef = useRef(
    value && !isTransparentColor(value) ? value : "#000000",
  );

  // Helper to expand 3-digit hex to 6-digit
  const expandHex = (hex) => {
    if (/^#[0-9A-Fa-f]{3}$/.test(hex)) {
      return "#" + hex[1] + hex[1] + hex[2] + hex[2] + hex[3] + hex[3];
    }
    return hex;
  };

  // Convert RGB to hex for the color input
  const rgbToHex = (rgb) => {
    if (!rgb || !rgb.startsWith("rgb(")) return rgb;

    try {
      const matches = rgb.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
      if (!matches) return rgb;

      const r = parseInt(matches[1]);
      const g = parseInt(matches[2]);
      const b = parseInt(matches[3]);

      return (
        "#" +
        r.toString(16).padStart(2, "0") +
        g.toString(16).padStart(2, "0") +
        b.toString(16).padStart(2, "0")
      );
    } catch (error) {
      return rgb;
    }
  };

  // Convert hex to RGB
  const hexToRgb = (hex) => {
    if (!hex || !hex.startsWith("#")) return hex;

    try {
      // Expand shorthand hex
      const fullHex = expandHex(hex);
      if (!/^#[0-9A-Fa-f]{6}$/.test(fullHex)) return hex;

      const r = parseInt(fullHex.slice(1, 3), 16);
      const g = parseInt(fullHex.slice(3, 5), 16);
      const b = parseInt(fullHex.slice(5, 7), 16);

      return `rgb(${r}, ${g}, ${b})`;
    } catch (error) {
      return hex;
    }
  };

  // Determine if value is RGB format
  const isRgbFormat = (color) => {
    return color && color.startsWith("rgb(");
  };

  // Get display value for color input (always hex)
  const getColorInputValue = (color) => {
    if (isRgbFormat(color)) {
      return rgbToHex(color);
    }
    return expandHex(color);
  };

  // Get display value for text input (preserves original format)
  const getTextInputValue = (color) => {
    return color || "#000000";
  };

  useEffect(() => {
    setLocalValue(value || "#000000");
    if (value && !isTransparentColor(value)) {
      lastColorRef.current = value;
    }
  }, [value]);

  const handleColorChange = (e) => {
    const newHexValue = e.target.value;
    setLocalValue(newHexValue);

    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    timeoutRef.current = setTimeout(() => {
      // If original value was RGB, convert back to RGB
      if (isRgbFormat(value)) {
        onChange(hexToRgb(newHexValue));
      } else {
        onChange(newHexValue);
      }
    }, delay);
  };

  const handleTextChange = (e) => {
    const newValue = e.target.value;
    setLocalValue(newValue);

    // Clear any pending debounced updates
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    // Validate and call onChange for both hex and RGB formats
    const isValidHex = /^#([0-9A-Fa-f]{3}){1,2}$/.test(newValue);
    const isValidRgb = /^rgb\(\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\)$/.test(newValue);

    if (isValidHex || isValidRgb) {
      timeoutRef.current = setTimeout(() => {
        onChange(newValue);
      }, delay);
    }
  };

  const handleTransparentToggle = (e) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
    if (e.target.checked) {
      onChange(TRANSPARENT);
    } else {
      // Leaving transparent: restore the color that was set before.
      const restored = lastColorRef.current || "#000000";
      setLocalValue(restored);
      onChange(restored);
    }
  };

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 0.5, width: "100%" }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "flex-start",
          gap: 1,
          width: "100%",
        }}
      >
        <TextField
          aria-label={label}
          variant="outlined"
          size="small"
          type="color"
          value={getColorInputValue(localValue)}
          onChange={handleColorChange}
          sx={{
            width: 48,
            flexShrink: 0,
            "& .MuiInputBase-root": { height: 34, minHeight: 34 },
            "& input": { height: 34, padding: "2px" },
          }}
          disabled={transparent}
        />
        <TextField
          label={label}
          variant="outlined"
          size="small"
          value={transparent ? TRANSPARENT : getTextInputValue(localValue)}
          onChange={handleTextChange}
          placeholder="#000000"
          sx={{ flex: 1, minWidth: 0 }}
          InputLabelProps={{ shrink: true }}
          disabled={transparent}
        />
      </Box>
      <FormControlLabel
        control={
          <Checkbox
            size="small"
            checked={transparent}
            onChange={handleTransparentToggle}
            sx={{ py: 0 }}
          />
        }
        label={t("datasets:label.transparent", "Transparent")}
        sx={{
          m: 0,
          mt: 1.5,
          "& .MuiFormControlLabel-label": { fontSize: "0.75rem" },
        }}
      />
    </Box>
  );
}
