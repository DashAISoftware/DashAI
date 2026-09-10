import React from "react";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import {
  MIN_INPUT_WIDTH,
  CHAR_WIDTH_PX,
  INPUT_PADDING_PX,
} from "./inputFieldConstants";

function computeWidth(val, placeholder) {
  const len = Math.max(
    String(val ?? "").length,
    String(placeholder ?? "").length,
  );
  return Math.max(MIN_INPUT_WIDTH, len * CHAR_WIDTH_PX + INPUT_PADDING_PX);
}

// Plain <input> styled to match the previous MUI TextField appearance.
// No Emotion per-mount cost - one static CSS class is enough.
const baseInputStyle = {
  fontSize: "0.875rem",
  padding: "6px 10px",
  border: "1px solid rgba(128,128,128,0.4)",
  borderRadius: 4,
  background: "transparent",
  color: "inherit",
  outline: "none",
  boxSizing: "border-box",
};

function InputField({
  handleChange,
  rowIndex,
  col,
  typeInfo,
  value,
  placeholder,
}) {
  const { dtype, type, categories } = typeInfo || {};
  const effectiveType = type || dtype || "string";
  const { t } = useTranslation(["prediction"]);
  const theme = useTheme();

  const inputStyle = {
    ...baseInputStyle,
    background: theme.palette.background.paper,
    color: theme.palette.text.primary,
  };

  const selectStyle = {
    ...inputStyle,
    minWidth: MIN_INPUT_WIDTH,
    cursor: "pointer",
    appearance: "none",
    WebkitAppearance: "none",
    paddingRight: 28,
    backgroundImage: `url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'%3E%3Cpath fill='${encodeURIComponent(theme.palette.text.secondary)}' d='M6 8L1 3h10z'/%3E%3C/svg%3E")`,
    backgroundRepeat: "no-repeat",
    backgroundPosition: "right 8px center",
  };

  if (effectiveType === "Categorical" && categories && categories.length > 0) {
    return (
      <select
        value={value || ""}
        onChange={(e) => handleChange(rowIndex, col, e.target.value)}
        style={selectStyle}
      >
        <option value="" disabled>
          {t("prediction:label.selectCategory")}
        </option>
        {categories.map((cat, idx) => (
          <option key={idx} value={cat}>
            {cat}
          </option>
        ))}
      </select>
    );
  }

  if (
    effectiveType === "Float" ||
    effectiveType === "Integer" ||
    dtype?.startsWith("float") ||
    dtype?.startsWith("int")
  ) {
    const isInteger = effectiveType === "Integer" || dtype?.startsWith("int");
    return (
      <input
        type="number"
        step={isInteger ? 1 : "any"}
        value={value ?? ""}
        placeholder={String(placeholder ?? "")}
        onChange={(e) => {
          const v =
            e.target.value === ""
              ? ""
              : isInteger
                ? parseInt(e.target.value, 10)
                : parseFloat(e.target.value);
          handleChange(rowIndex, col, v);
        }}
        style={{ ...inputStyle, width: computeWidth(value, placeholder) }}
      />
    );
  }

  if (effectiveType === "Image" || dtype === "image") {
    return (
      <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
        {value instanceof File && (
          <img
            src={URL.createObjectURL(value)}
            alt="preview"
            style={{
              maxHeight: 40,
              maxWidth: 40,
              objectFit: "contain",
              borderRadius: 4,
            }}
          />
        )}
        <label
          style={{
            ...inputStyle,
            display: "inline-flex",
            alignItems: "center",
            cursor: "pointer",
            fontSize: "0.8rem",
            width: "auto",
          }}
        >
          {value instanceof File
            ? t("prediction:label.changeImage")
            : t("prediction:label.uploadImage")}
          <input
            type="file"
            accept="image/*"
            hidden
            onChange={(e) => {
              const file = e.target.files?.[0];
              if (file) handleChange(rowIndex, col, file);
            }}
          />
        </label>
      </div>
    );
  }

  return (
    <input
      type="text"
      value={value ?? ""}
      placeholder={String(placeholder ?? "")}
      onChange={(e) => handleChange(rowIndex, col, e.target.value)}
      style={{ ...inputStyle, width: computeWidth(value, placeholder) }}
    />
  );
}

export default React.memo(InputField);
