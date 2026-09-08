import React, { useState } from "react";
import { Box, Chip, Typography, useTheme } from "@mui/material";
import {
  Description,
  PictureAsPdf,
  InsertDriveFile,
  Article,
} from "@mui/icons-material";
import { useTranslation } from "react-i18next";

/**
 * Returns the appropriate MUI icon component for the given file type.
 * @param {string} fileType - File extension (e.g. "pdf", "txt").
 * @returns {React.ElementType} An icon component.
 */
const getDocumentIcon = (fileType) => {
  const iconMap = {
    pdf: PictureAsPdf,
    txt: Article,
  };

  const IconComponent = iconMap[fileType?.toLowerCase()] || InsertDriveFile;
  return IconComponent;
};

/**
 * A single clickable document row with icon and metadata, shown inside a list.
 *
 * @param {object}  props
 * @param {object}  props.document - The document object ({ id, name, type, ... }).
 * @param {boolean} [props.disabled=false] - Whether the item is greyed out and non-interactive.
 * @param {function} [props.onClick] - Click handler for the item.
 * @param {object}  [props.indexState] - This document's indexing state within
 *   the session (`{ chunks, indexed }`), as reported by the backend.
 * @returns {JSX.Element}
 */
export default function DocumentListItem({
  document,
  disabled = false,
  onClick,
  indexState,
}) {
  const { t } = useTranslation(["generative"]);
  const [isHovered, setIsHovered] = useState(false);
  const theme = useTheme();

  const DocumentIcon = getDocumentIcon(document.type);
  const colorMap = { pdf: "primary.main", txt: "primary.main" };
  const documentColor =
    colorMap[document.type?.toLowerCase()] || theme.palette.text.disabled;

  const disabledOverlay = `repeating-linear-gradient(45deg, transparent, transparent 10px, ${theme.palette.action.disabled} 10px, ${theme.palette.action.disabled} 20px)`;

  return (
    <Box
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
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
          <Typography
            variant="caption"
            sx={{
              color: disabled ? "text.disabled" : "text.secondary",
              textTransform: "uppercase",
            }}
          >
            {document.type || t("generative:rag.documents.table.unknownType")}
          </Typography>
          {indexState && (
            <Chip
              size="small"
              variant="outlined"
              color={indexState.indexed ? "success" : "default"}
              label={
                indexState.indexed
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
    </Box>
  );
}
