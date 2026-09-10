import React, { useState } from "react";
import { Box, Typography, Tooltip, Stack } from "@mui/material";
import { VpnKeyOutlined as KeyIcon } from "@mui/icons-material";
import HoverToolInfo from "./HoverToolInfo";
import api from "../../../api/api";
import { CategoryIcon } from "./CategoryIcon";
import { useTranslation } from "react-i18next";
import { useTheme } from "@mui/material/styles";
import { setCustomDragImage } from "../../../utils/dragImage";
import ModelDownloadStatusIcon from "../../models/model/ModelDownloadStatusIcon";
import { useToolGate } from "./useToolGate";

export default function ToolGridItem({
  tool,
  disabled,
  onUse,
  onDownload,
  onNeedsCredentials,
}) {
  const [anchorEl, setAnchorEl] = useState(null);
  const [hoveredTool, setHoveredTool] = useState(null);
  const { t } = useTranslation(["common", "credentials"]);
  const theme = useTheme();

  const gate = useToolGate({ ...tool, disabled });

  const handleClick = () =>
    gate.resolve({ onUse, onDownload, onNeedsCredentials });

  const handleMouseEnter = (event, tool) => {
    if (!disabled) {
      setAnchorEl(event.currentTarget);
      setHoveredTool(tool);
    }
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
    <>
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
            position: "relative",
            bgcolor: gate.blocked
              ? theme.palette.ui.disabled
              : theme.palette.ui.box,
            border: `1px solid ${theme.palette.ui.border}`,
            borderRadius: 1.5,
            overflow: "hidden",
            cursor: gate.blocked
              ? gate.gated
                ? "pointer"
                : "not-allowed"
              : "grab",
            transition: "all 0.2s",
            "&:hover": {
              bgcolor: disabled
                ? theme.palette.ui.disabled
                : theme.palette.action.hover,
              borderColor: disabled
                ? theme.palette.ui.border
                : tool.metadata.color,
              transform: disabled ? "none" : "translateY(-4px)",
              boxShadow: disabled ? "none" : `0 8px 16px rgba(0, 0, 0, 0.2)`,
            },
            "&::after": gate.blocked
              ? {
                  content: '""',
                  position: "absolute",
                  inset: 0,
                  borderRadius: 1.5,
                  pointerEvents: "none",
                  background:
                    "repeating-linear-gradient(45deg, transparent, transparent 10px, rgba(0, 0, 0, 0.1) 10px, rgba(0, 0, 0, 0.1) 20px)",
                  zIndex: 2,
                }
              : {},
          }}
        >
          {/* Preview Image — dimmed when blocked; the download/credential icons
              below are kept out of every dimmed subtree so they keep full
              color. */}
          <Box
            sx={{
              width: "100%",
              height: 100,
              bgcolor: gate.blocked
                ? theme.palette.ui.disabled
                : theme.palette.ui.border,
              borderBottom: `1px solid ${
                gate.blocked
                  ? theme.palette.ui.disabled
                  : theme.palette.ui.border
              }`,
              opacity: gate.blocked ? 0.5 : 1,
              filter: gate.blocked ? "grayscale(0.6)" : "none",
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

          {/* Content */}
          <Box sx={{ p: 3 }}>
            {/* Icon and Badges */}
            <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "center",
                  width: 28,
                  height: 28,
                  p: 4,
                  borderRadius: 0.75,
                  bgcolor: gate.blocked
                    ? theme.palette.ui.disabled
                    : theme.palette.ui.border,
                  color: gate.blocked
                    ? theme.palette.text.disabled
                    : theme.palette.text.primary,
                  flexShrink: 0,
                  opacity: gate.blocked ? 0.5 : 1,
                  filter: gate.blocked ? "grayscale(0.6)" : "none",
                }}
              >
                <CategoryIcon
                  icon={tool.metadata.icon}
                  color={
                    gate.blocked
                      ? theme.palette.text.disabled
                      : tool.metadata.color
                  }
                />
              </Box>

              {action && (
                <Box
                  draggable={false}
                  sx={{
                    ml: "auto",
                    display: "flex",
                    alignItems: "center",
                    flexShrink: 0,
                    zIndex: 3,
                  }}
                >
                  {action}
                </Box>
              )}
            </Box>

            {/* Title */}
            <Typography
              variant="body2"
              sx={{
                color: gate.blocked
                  ? theme.palette.text.disabled
                  : theme.palette.text.primary,
                fontWeight: 500,
                mb: 1,
                opacity: gate.blocked ? 0.5 : 1,
                overflow: "hidden",
                textOverflow: "ellipsis",
                display: "-webkit-box",
                WebkitLineClamp: 2,
                WebkitBoxOrient: "vertical",
                lineHeight: 1.3,
                minHeight: "2.6em",
              }}
            >
              {tool.display_name || tool.name}
            </Typography>

            {/* Category */}
            <Typography
              variant="caption"
              sx={{
                color: gate.blocked
                  ? theme.palette.text.disabled
                  : theme.palette.text.primary,
                opacity: gate.blocked ? 0.5 : 1,
              }}
            >
              {tool.metadata.category ?? t("common:other")}
            </Typography>
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
    </>
  );
}
