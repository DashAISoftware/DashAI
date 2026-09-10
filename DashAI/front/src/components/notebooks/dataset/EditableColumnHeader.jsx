import { useState, useRef, useEffect } from "react";
import {
  Typography,
  TextField,
  Box,
  Tooltip,
  Chip,
  Menu,
  MenuItem,
} from "@mui/material";
import { useTranslation } from "react-i18next";

const ENCODER_OPTIONS = ["one_hot", "label"];

/**
 * Editable column header component that allows users to rename dataset columns
 * and change the encoder for Categorical columns.
 *
 * @param {string} columnName - Current name of the column
 * @param {string} columnType - Type of the column (e.g., "Integer", "Text")
 * @param {string|null} columnEncoder - Encoder for Categorical columns (null for non-categorical)
 * @param {Function} onRename - Callback function when rename is confirmed (oldName, newName) => Promise
 * @param {Function|null} onEncoderChange - Callback when encoder changes (colName, encoder) => Promise
 * @param {boolean} disabled - Whether editing is disabled
 */
export default function EditableColumnHeader({
  columnName,
  columnType,
  columnEncoder = null,
  onRename,
  onEncoderChange = null,
  disabled = false,
}) {
  const [isEditing, setIsEditing] = useState(false);
  const [editValue, setEditValue] = useState(columnName);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");
  const [encoderAnchor, setEncoderAnchor] = useState(null);
  const [encoderLoading, setEncoderLoading] = useState(false);
  const [encoderError, setEncoderError] = useState("");
  const inputRef = useRef(null);
  const { t } = useTranslation(["common"]);

  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [isEditing]);

  const handleEditClick = () => {
    if (disabled) return;
    setEditValue(columnName);
    setError("");
    setIsEditing(true);
  };

  const handleCancel = () => {
    setEditValue(columnName);
    setError("");
    setIsEditing(false);
  };

  const handleConfirm = async () => {
    const newName = editValue.trim();
    if (!newName) {
      setError(t("common:columnNameEmpty"));
      return;
    }
    if (newName === columnName) {
      setIsEditing(false);
      return;
    }
    if (!/^[a-zA-Z0-9_]+$/.test(newName)) {
      setError(t("common:columnNameInvalid"));
      return;
    }

    setIsLoading(true);
    setError("");

    try {
      await onRename(columnName, newName);
      setIsEditing(false);
    } catch (err) {
      setError(
        err.response?.data?.detail ||
          err.message ||
          t("common:errorRenamingColumn"),
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === "Enter") {
      handleConfirm();
    } else if (e.key === "Escape") {
      handleCancel();
    }
  };

  const handleEncoderClick = (e) => {
    e.stopPropagation();
    if (!disabled && onEncoderChange) {
      setEncoderAnchor(e.currentTarget);
    }
  };

  const handleEncoderClose = () => setEncoderAnchor(null);

  const handleEncoderSelect = async (newEncoder) => {
    setEncoderAnchor(null);
    if (newEncoder === columnEncoder) return;
    setEncoderLoading(true);
    setEncoderError("");
    try {
      await onEncoderChange(columnName, newEncoder);
    } catch (err) {
      setEncoderError(
        err.response?.data?.detail ||
          err.message ||
          t("common:errorChangingEncoder"),
      );
    } finally {
      setEncoderLoading(false);
    }
  };

  const encoderLabel = (enc) => {
    if (enc === "one_hot") return t("common:encoderOneHot");
    if (enc === "label") return t("common:encoderLabel");
    return enc;
  };

  if (isEditing) {
    return (
      <Box
        sx={{
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          width: "100%",
          gap: 1,
        }}
      >
        <TextField
          inputRef={inputRef}
          value={editValue}
          onChange={(e) => setEditValue(e.target.value)}
          onKeyDown={handleKeyDown}
          onBlur={handleConfirm}
          size="small"
          error={!!error}
          disabled={isLoading}
          sx={{
            width: "100%",
            "& .MuiInputBase-input": {
              fontSize: "0.875rem",
              paddingY: 1,
              textAlign: "center",
            },
          }}
        />
        {error && (
          <Typography variant="body2" color="error">
            {error}
          </Typography>
        )}
        <Typography variant="body2" color="text.secondary">
          {isLoading ? t("common:loading") : columnType || t("common:unknown")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        alignItems: "center",
        width: "100%",
        gap: 1,
        textAlign: "center",
      }}
    >
      <Tooltip title={!disabled ? t("common:renameColumn") : ""} arrow>
        <Typography
          variant="body1"
          onDoubleClick={!disabled ? handleEditClick : undefined}
          sx={{
            fontWeight: "bold",
            cursor: !disabled ? "pointer" : "default",
            transition: "all 0.2s",
            "&:hover": !disabled
              ? { color: "primary.main", textDecoration: "underline" }
              : {},
          }}
        >
          {columnName}
        </Typography>
      </Tooltip>
      <Typography variant="body2" color="text.secondary">
        {columnType || t("common:unknown")}
      </Typography>

      {/* Encoder chip - only for Categorical columns */}
      {columnType === "Categorical" && columnEncoder && (
        <>
          <Tooltip title={t("common:changeEncoder")} arrow>
            <span style={{ display: "inline-flex" }}>
              <Chip
                label={encoderLoading ? "..." : encoderLabel(columnEncoder)}
                size="small"
                onClick={handleEncoderClick}
                disabled={disabled || !onEncoderChange}
                aria-label={t("common:encoder")}
                sx={{
                  fontSize: "0.65rem",
                  height: "18px",
                  cursor: onEncoderChange && !disabled ? "pointer" : "default",
                }}
              />
            </span>
          </Tooltip>
          {encoderError && (
            <Typography variant="body2" color="error">
              {encoderError}
            </Typography>
          )}
          <Menu
            anchorEl={encoderAnchor}
            open={Boolean(encoderAnchor)}
            onClose={handleEncoderClose}
          >
            {ENCODER_OPTIONS.map((enc) => (
              <MenuItem
                key={enc}
                selected={enc === columnEncoder}
                onClick={() => handleEncoderSelect(enc)}
                sx={{ fontSize: "0.85rem" }}
              >
                {encoderLabel(enc)}
              </MenuItem>
            ))}
          </Menu>
        </>
      )}
    </Box>
  );
}
