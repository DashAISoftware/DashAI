import React from "react";
import { Box, Chip, Typography, useTheme } from "@mui/material";
import { Description as DocumentIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";

/**
 * A single clickable document row with icon and metadata, shown inside a list.
 *
 * @param {object}  props
 * @param {object}  props.document - The document object ({ id, name, ... }).
 * @param {boolean} [props.disabled=false] - Whether the item is greyed out and non-interactive.
 * @param {function} [props.onClick] - Click handler for the item.
 * @param {object}  [props.indexState] - This document's indexing state within
 *   the session (`{ chunks, indexed }`), as reported by the backend.
 * @param {node}    [props.actions] - Controls shown at the end of
 *   the row. They stop their own clicks, so acting on a row does not also
 *   trigger the row itself.
 * @returns {JSX.Element}
 */
export default function DocumentListItem({
  document,
  disabled = false,
  onClick,
  indexState,
  actions,
}) {
  const { t } = useTranslation(["generative"]);
  const theme = useTheme();

  const documentColor = theme.palette.primary.main;

  const disabledOverlay = `repeating-linear-gradient(45deg, transparent, transparent 10px, ${theme.palette.action.disabled} 10px, ${theme.palette.action.disabled} 20px)`;

  return (
    <Box
      onClick={disabled ? null : onClick}
      sx={{
        display: "flex",
        alignItems: "center",
        gap: 1.5,
        p: 1.5,
        width: "100%",
        minWidth: 0,
        maxWidth: "100%",
        bgcolor: disabled ? "action.disabledBackground" : "background.paper",
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        cursor: disabled ? "not-allowed" : "pointer",
        transition: "all 0.2s",
        opacity: disabled ? 0.5 : 1,
        filter: disabled ? "grayscale(0.6)" : "none",
        position: "relative",
        "&:hover": {
          bgcolor: disabled ? "action.disabledBackground" : "action.hover",
          borderColor: disabled ? "divider" : documentColor,
          transform: disabled ? "none" : "translateX(4px)",
        },
        "&::after": disabled
          ? {
              content: '""',
              position: "absolute",
              inset: 0,
              borderRadius: 1,
              pointerEvents: "none",
              background: disabledOverlay,
            }
          : {},
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          width: 36,
          height: 36,
          borderRadius: 1,
          bgcolor: "action.selected",
          color: disabled ? "text.disabled" : "text.primary",
          flexShrink: 0,
          transition: "all 0.2s",
        }}
      >
        <DocumentIcon sx={{ fontSize: 20 }} />
      </Box>

      <Box sx={{ flex: 1, minWidth: 0 }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            mb: 0.5,
          }}
        >
          <Typography
            variant="body2"
            sx={{
              color: disabled ? "text.disabled" : "text.primary",
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {document.name}
          </Typography>
        </Box>
        <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
          {indexState && (
            <Chip
              size="small"
              variant="outlined"
              color={
                indexState.indexing
                  ? "info"
                  : indexState.indexed
                    ? "success"
                    : "default"
              }
              label={
                // Indexing wins over the chunk count: those chunks belong to
                // the configuration being replaced, so showing them as ready
                // would promise an answer the pipeline cannot give yet.
                indexState.indexing
                  ? t("generative:rag.index.indexing")
                  : indexState.indexed
                    ? t("generative:rag.index.chunkCount", {
                        count: indexState.chunks,
                      })
                    : t("generative:rag.index.notIndexed")
              }
              sx={{
                height: 18,
                "& .MuiChip-label": { px: 0.75, fontSize: 10 },
              }}
            />
          )}
        </Box>
      </Box>

      {actions && (
        <Box
          onClick={(event) => event.stopPropagation()}
          sx={{
            display: "flex",
            alignItems: "center",
            flexShrink: 0,
          }}
        >
          {actions}
        </Box>
      )}
    </Box>
  );
}
