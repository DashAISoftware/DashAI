import React from "react";
import { Box, Typography, Popover } from "@mui/material";
import { useTranslation } from "react-i18next";
import { useTheme } from "@mui/material/styles";

const formatSize = (bytes) => {
  if (bytes == null) return null;
  const mb = bytes / 1024 / 1024;
  if (mb >= 1024) return `${(mb / 1024).toFixed(1)} GB`;
  return `${Math.round(mb)} MB`;
};

export default function HoverModelInfo({
  anchorEl,
  hoveredModel,
  handleMouseLeave,
}) {
  const { t } = useTranslation(["common", "custom"]);
  const theme = useTheme();
  const size = formatSize(
    hoveredModel?.metadata?.download_size_bytes ||
      hoveredModel?.download_size_bytes,
  );

  return (
    <Popover
      open={Boolean(anchorEl)}
      anchorEl={anchorEl}
      onClose={handleMouseLeave}
      anchorOrigin={{
        vertical: "center",
        horizontal: "left",
      }}
      transformOrigin={{
        vertical: "center",
        horizontal: "right",
      }}
      disableRestoreFocus
      sx={{
        pointerEvents: "none",
        "& .MuiPopover-paper": {
          bgcolor: theme.palette.background.paper,
          border: `1px solid ${theme.palette.divider}`,
          borderRadius: 2,
          p: 4,
          maxWidth: 320,
          ml: -2,
        },
      }}
    >
      {hoveredModel && (
        <Box>
          {/* Title */}
          <Typography
            variant="subtitle2"
            sx={{ color: theme.palette.text.primary, fontWeight: 600, mb: 2 }}
          >
            {hoveredModel.display_name || hoveredModel.name}
          </Typography>

          {/* Description */}
          <Typography
            variant="body2"
            sx={{ color: theme.palette.text.secondary, lineHeight: 1.5 }}
          >
            {hoveredModel.description ||
              hoveredModel.metadata?.description ||
              t("common:noDescription")}
          </Typography>

          {size && (
            <Typography
              variant="caption"
              sx={{
                display: "block",
                mt: 2,
                color: theme.palette.text.secondary,
              }}
            >
              {t("custom:modelSize", { size })}
            </Typography>
          )}
        </Box>
      )}
    </Popover>
  );
}
