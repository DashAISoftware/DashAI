import React, { useState } from "react";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import HoverModelInfo from "./HoverModelInfo";
import { ModelIcon } from "./ModelIcon";
import { setCustomDragImage } from "../../../utils/dragImage";

export default function ModelListItem({
  model,
  disabled = false,
  draggable = true,
  dragType = "application/x-dashai-model",
  dragPayload,
  onClick,
  onDisabledClick,
  action = null,
  ...props
}) {
  const theme = useTheme();
  const [anchorEl, setAnchorEl] = useState(null);
  const [hoveredModel, setHoveredModel] = useState(null);

  const handleMouseEnter = (event, model) => {
    setAnchorEl(event.currentTarget);
    setHoveredModel(model);
  };

  const handleMouseLeave = () => {
    setAnchorEl(null);
    setHoveredModel(null);
  };

  const handleCardClick = (event) => {
    if (disabled) {
      if (onDisabledClick) onDisabledClick(event);
      return;
    }
    if (onClick) onClick(event);
  };

  const isClickable = Boolean(onClick || onDisabledClick);

  // Get color and icon from metadata or use defaults
  const color =
    model.color || model.metadata?.color || theme.palette.text.secondary;
  const iconName = model.metadata?.icon || "Science";

  return (
    <>
      <Box
        key={model.id}
        draggable={!disabled && draggable}
        onDragStart={
          !disabled && draggable
            ? (e) => {
                e.dataTransfer.setData(
                  dragType,
                  JSON.stringify(dragPayload ?? model),
                );
                e.dataTransfer.effectAllowed = "copy";
                setCustomDragImage(e);
              }
            : undefined
        }
        onMouseEnter={(e) => handleMouseEnter(e, model)}
        onMouseLeave={handleMouseLeave}
        // Close the hover popover on any click in the row (capture phase, so it
        // runs even for the action's icon which stops propagation). Otherwise a
        // click that opens a modal (e.g. delete confirmation) leaves the popover
        // stuck open since no mouseleave fires.
        onClickCapture={handleMouseLeave}
        onClick={handleCardClick}
        {...props}
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 3,
          p: 3,
          bgcolor: disabled ? theme.palette.ui.disabled : theme.palette.ui.box,
          border: `1px solid ${theme.palette.ui.border}`,
          borderRadius: 1,
          cursor: isClickable ? "pointer" : "default",
          transition: "all 0.2s",
          position: "relative",
          "&:hover": {
            bgcolor: disabled
              ? theme.palette.ui.disabled
              : theme.palette.action.hover,
            // A not downloaded row is disabled but still clickable to start the
            // download, so give it the same hover feedback (border highlight +
            // slide) instead of feeling stiff.
            borderColor: color,
            transform: !isClickable ? "none" : "translateX(4px)",
          },
          "&::after": disabled
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
        {/* Icon */}
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            width: 36,
            height: 36,
            borderRadius: 1,
            bgcolor: disabled
              ? theme.palette.ui.disabled
              : theme.palette.ui.border,
            color: disabled
              ? theme.palette.text.disabled
              : theme.palette.text.primary,
            flexShrink: 0,
          }}
        >
          <ModelIcon
            iconName={iconName}
            color={disabled ? theme.palette.text.disabled : color}
          />
        </Box>

        {/* Content */}
        <Box sx={{ flex: 1, minWidth: 0 }}>
          <Typography
            variant="body2"
            sx={{
              color: disabled
                ? theme.palette.text.disabled
                : theme.palette.text.primary,
              fontWeight: 500,
              overflow: "hidden",
              textOverflow: "ellipsis",
              whiteSpace: "nowrap",
            }}
          >
            {model.display_name || model.name}
          </Typography>
        </Box>

        {/* Trailing action (e.g. download/delete control) */}
        {action && (
          <Box
            draggable={false}
            sx={{ flexShrink: 0, display: "flex", alignItems: "center" }}
          >
            {action}
          </Box>
        )}
      </Box>
      {
        <HoverModelInfo
          anchorEl={anchorEl}
          hoveredModel={hoveredModel}
          handleMouseLeave={handleMouseLeave}
        />
      }
    </>
  );
}
