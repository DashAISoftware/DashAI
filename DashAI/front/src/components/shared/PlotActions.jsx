import { useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  Tooltip,
  Menu,
  MenuItem,
  Dialog,
} from "@mui/material";
import Plot from "react-plotly.js";
import DownloadIcon from "@mui/icons-material/Download";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import CloseIcon from "@mui/icons-material/Close";
import { alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { downloadArtifact } from "../../utils/downloadArtifact";

// Fill 75% of the viewport, matching ArtifactViewer's fullscreen sizing.
const fullscreenHeight =
  typeof window !== "undefined"
    ? Math.max(360, Math.round(window.innerHeight * 0.75) - 64)
    : 720;

/**
 * Download + fullscreen affordance for a plain (non artifact) Plotly chart -
 * Live Metrics panels and session comparison graphs build their `data`/
 * `layout` client side from raw metrics, so they have no backend artifact to
 * hand ArtifactViewer. This reuses the same PNG/SVG export plumbing
 * (`downloadArtifact`) and the same lightbox look, without the edit chrome
 * those charts don't need.
 */
export default function PlotActions({
  getContainer,
  data,
  layout,
  filename,
  sx,
}) {
  const { t } = useTranslation(["explainers", "common"]);
  const [anchorEl, setAnchorEl] = useState(null);
  const [fullscreen, setFullscreen] = useState(false);

  const actionButtonSx = {
    color: "text.secondary",
    "&:hover": { color: "text.primary" },
  };

  const handleDownload = (format) => {
    setAnchorEl(null);
    const container = getContainer();
    const plotEl = container?.querySelector(".js-plotly-plot");
    if (!plotEl) return;
    downloadArtifact({ type: "plotly", title: filename }, { plotEl, format });
  };

  return (
    <>
      <Box
        className="plot-actions"
        sx={{
          display: "flex",
          gap: 0.5,
          p: 0.5,
          borderRadius: 1,
          bgcolor: (theme) => alpha(theme.palette.background.paper, 0.85),
          backdropFilter: "blur(4px)",
          border: (theme) => `1px solid ${theme.palette.ui.border}`,
          ...sx,
        }}
      >
        <Tooltip title={t("explainers:button.download")}>
          <IconButton
            size="small"
            onClick={(e) => setAnchorEl(e.currentTarget)}
            sx={actionButtonSx}
          >
            <DownloadIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title={t("explainers:button.fullscreen")}>
          <IconButton
            size="small"
            onClick={() => setFullscreen(true)}
            sx={actionButtonSx}
          >
            <FullscreenIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Menu
        anchorEl={anchorEl}
        open={Boolean(anchorEl)}
        onClose={() => setAnchorEl(null)}
      >
        <MenuItem onClick={() => handleDownload("png")}>
          {t("explainers:button.downloadPng")}
        </MenuItem>
        <MenuItem onClick={() => handleDownload("svg")}>
          {t("explainers:button.downloadSvg")}
        </MenuItem>
      </Menu>

      <Dialog
        open={fullscreen}
        fullScreen
        onClose={() => setFullscreen(false)}
        transitionDuration={0}
        keepMounted
        slotProps={{
          paper: {
            elevation: 0,
            sx: {
              bgcolor: "rgba(0, 0, 0, 0.15)",
              backgroundImage: "none",
              backdropFilter: "blur(6px)",
              willChange: "backdrop-filter",
              boxShadow: "none",
            },
          },
        }}
      >
        <Box
          onClick={(e) => {
            if (e.target === e.currentTarget) setFullscreen(false);
          }}
          sx={{
            position: "relative",
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
          }}
        >
          <IconButton
            onClick={() => setFullscreen(false)}
            aria-label={t("common:close")}
            sx={{
              position: "absolute",
              top: 16,
              right: 16,
              zIndex: 1,
              width: 36,
              height: 36,
              color: "#fff",
              bgcolor: "rgba(255, 255, 255, 0.12)",
              border: "1px solid rgba(255, 255, 255, 0.2)",
              "&:hover": { bgcolor: "rgba(255, 255, 255, 0.25)" },
            }}
          >
            <CloseIcon sx={{ fontSize: 18 }} />
          </IconButton>

          <Box
            sx={{
              width: "75vw",
              maxHeight: "75vh",
              overflow: "auto",
              bgcolor: "background.paper",
              borderRadius: "10px",
              boxShadow: "0 30px 80px rgba(0, 0, 0, 0.6)",
              p: 4,
            }}
          >
            {fullscreen && (
              <Plot
                data={data}
                layout={{ ...layout, autosize: true, height: fullscreenHeight }}
                useResizeHandler
                style={{ width: "100%" }}
                config={{ responsive: true, displayModeBar: false }}
              />
            )}
          </Box>
        </Box>
      </Dialog>
    </>
  );
}

PlotActions.propTypes = {
  getContainer: PropTypes.func.isRequired,
  data: PropTypes.array.isRequired,
  layout: PropTypes.object,
  filename: PropTypes.string,
  sx: PropTypes.object,
};
