import React, { useState } from "react";
import { Box, Typography, Tooltip, Stack } from "@mui/material";
import { VpnKeyOutlined as KeyIcon } from "@mui/icons-material";
import { useTheme } from "@mui/material/styles";
import HoverToolInfo from "./HoverToolInfo";
import api from "../../../api/api";
import { CategoryIcon } from "./CategoryIcon";
import { useTranslation } from "react-i18next";
import { setCustomDragImage } from "../../../utils/dragImage";
import ModelDownloadStatusIcon from "../../models/model/ModelDownloadStatusIcon";
import { useToolGate } from "./useToolGate";

export default function ToolListItem({
  tool,
  disabled = false,
  onUse,
  onDownload,
  onNeedsCredentials,
  ...props
}) {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState(null);
  const [hoveredTool, setHoveredTool] = useState(null);
  const { t } = useTranslation(["common", "credentials"]);

  const gate = useToolGate({ ...tool, disabled });

  const handleClick = () =>
    gate.resolve({ onUse, onDownload, onNeedsCredentials });

  const handleMouseEnter = (event, tool) => {
    if (!disabled) {
      setAnchorEl(event.currentTarget);
      setHoveredTool(tool);
    }
  };

  const getTourAttribute = () => {
    if (tool.name === "HistogramPlotExplorer") {
      return "histogram-explorer";
    }
    if (tool.name === "LabelEncoder") {
      return "label-encoder-converter";
    }
    if (tool.name === "NanRemover") {
      return "nan-remover-converter";
    }
    return undefined;
  };

  const handleMouseLeave = () => {
    setAnchorEl(null);
    setHoveredTool(null);
  };

  const action =
    gate.locked || gate.requiresDownload ? (
      <Stack direction="row" spacing={0.5} alignItems="center">
        {gate.locked && (
          <Tooltip
            title={t("credentials:requiredTooltip", {
              platform: gate.requiredPlatforms,
            })}
          >
            <KeyIcon fontSize="small" color="warning" />
          </Tooltip>
        )}
        {gate.requiresDownload && (
          <ModelDownloadStatusIcon model={tool} disabled={gate.locked} />
        )}
      </Stack>
    ) : null;

  return (
    <Box sx={{ display: "flex", alignItems: "center", gap: 6 }}>
      <Tooltip
        title={disabled && tool.tooltip ? tool.tooltip : tool.description}
        arrow
        placement="top"
        slotProps={{
          tooltip: {
            sx: {
              bgcolor: theme.palette.background.paper,
              color: theme.palette.text.primary,
              display: disabled ? "block" : "none",
              border: `1px solid ${theme.palette.divider}`,
              fontSize: "0.75rem",
              maxWidth: 300,
              "& .MuiTooltip-arrow": {
                color: theme.palette.background.paper,
                "&::before": {
                  border: `1px solid ${theme.palette.divider}`,
                },
              },
            },
          },
        }}
      >
        <Box
          key={tool.id}
          data-tour={getTourAttribute()}
          {...props}
          draggable={!gate.blocked}
          onDragStart={
            !gate.blocked
              ? (e) => {
                  e.dataTransfer.setData(
                    "application/x-dashai-tool",
                    JSON.stringify(tool),
                  );
                  e.dataTransfer.effectAllowed = "copy";
                  setCustomDragImage(e);
                }
              : undefined
          }
          onMouseEnter={(e) => handleMouseEnter(e, tool)}
          onMouseLeave={handleMouseLeave}
          onClick={handleClick}
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 6,
            p: 6,
            flex: 1,
            minWidth: 0,
            bgcolor: gate.blocked
              ? theme.palette.ui.disabled
              : theme.palette.ui.box,
            border: `1px solid ${theme.palette.ui.border}`,
            borderRadius: 1,
            cursor: gate.blocked
              ? gate.gated
                ? "pointer"
                : "not-allowed"
              : "grab",
            transition: "all 0.2s",
            position: "relative",
            "&:hover": {
              bgcolor: disabled
                ? theme.palette.ui.disabled
                : theme.palette.action.hover,
              borderColor: disabled
                ? theme.palette.ui.border
                : tool.metadata.color,
              transform: disabled ? "none" : "translateX(4px)",
            },
            "&::after": gate.blocked
              ? {
                  content: '""',
                  position: "absolute",
                  inset: 0,
                  borderRadius: 1,
                  pointerEvents: "none",
                  background:
                    "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0, 0, 0, 0.1) 10px, rgba(0, 0, 0, 0.1) 20px)",
                }
              : {},
          }}
        >
          {/* Content (tool icon, text) dimmed when the card is blocked; the
              download/credential icons below stay outside it so they keep full
              color. */}
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              gap: 6,
              flex: 1,
              minWidth: 0,
              opacity: gate.blocked ? 0.5 : 1,
              filter: gate.blocked ? "grayscale(0.6)" : "none",
            }}
          >
            {/* Icon */}
            <Box
              sx={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                width: 36,
                height: 36,
                borderRadius: 1,
                bgcolor: gate.blocked
                  ? theme.palette.ui.disabled
                  : theme.palette.ui.border,
                color: gate.blocked
                  ? theme.palette.text.disabled
                  : theme.palette.text.primary,
                flexShrink: 0,
              }}
            >
              <CategoryIcon
                icon={tool.metadata.icon}
                color={tool.metadata.color}
              />
            </Box>

            {/* Content */}
            <Box sx={{ flex: 1, minWidth: 0 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  mb: 2,
                }}
              >
                <Typography
                  variant="body2"
                  sx={{
                    color: gate.blocked
                      ? theme.palette.text.disabled
                      : theme.palette.text.primary,
                    fontWeight: 500,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    width: 0,
                    flexGrow: 1,
                    whiteSpace: "nowrap",
                  }}
                >
                  {tool.display_name || tool.name}
                </Typography>
              </Box>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 4,
                  mb: 2,
                }}
              >
                <Typography
                  variant="caption"
                  sx={{
                    color: gate.blocked
                      ? theme.palette.text.disabled
                      : theme.palette.text.secondary,
                    overflow: "hidden",
                    textOverflow: "ellipsis",
                    width: 0,
                    flexGrow: 1,
                    whiteSpace: "nowrap",
                  }}
                >
                  {tool.metadata.category ?? t("common:other")}
                </Typography>
              </Box>
            </Box>
          </Box>

          {/* Download/credential status — left of the thumbnail, full color */}
          {action && (
            <Box
              draggable={false}
              sx={{
                flexShrink: 0,
                display: "flex",
                alignItems: "center",
                zIndex: 1,
              }}
            >
              {action}
            </Box>
          )}

          {/* Preview Thumbnail */}
          <Box
            sx={{
              width: 60,
              height: 40,
              borderRadius: 0.75,
              bgcolor: gate.blocked
                ? theme.palette.ui.disabled
                : theme.palette.ui.border,
              border: `1px solid ${
                gate.blocked
                  ? theme.palette.ui.disabled
                  : theme.palette.ui.border
              }`,
              display: { xs: "none", lg: "none", xl: "block" },
              overflow: "hidden",
              flexShrink: 0,
            }}
          >
            <img
              src={`${api.defaults.baseURL}/v1/component/image/${tool.name}/`}
              alt={tool.display_name}
              style={{
                width: "100%",
                height: "100%",
                objectFit: "cover",
                opacity: gate.blocked ? 0.4 : 1,
              }}
            />
          </Box>
        </Box>
      </Tooltip>

      {!disabled && (
        <HoverToolInfo
          anchorEl={anchorEl}
          hoveredTool={hoveredTool}
          handleMouseLeave={handleMouseLeave}
        />
      )}
    </Box>
  );
}
