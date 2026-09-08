import React, { useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  Menu,
  MenuItem,
  Typography,
  Tooltip,
  Dialog,
  Divider,
} from "@mui/material";
import DownloadIcon from "@mui/icons-material/Download";
import EditIcon from "@mui/icons-material/Edit";
import FullscreenIcon from "@mui/icons-material/Fullscreen";
import RestartAltIcon from "@mui/icons-material/RestartAlt";
import CloseIcon from "@mui/icons-material/Close";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import { useTheme, alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";

import ArtifactRenderer from "./ArtifactRenderer";
import PlotLayoutForm from "../notebooks/explorer/plotLayout/PlotLayoutForm";
import PlotlyJsonVisualizer from "../notebooks/explorer/visualizations/PlotlyJsonVisualizer";
import { applyThemeToLayout } from "../../utils/plotlyTheme";
import { downloadArtifact } from "../../utils/downloadArtifact";

/**
 * Renders one typed artifact as a self contained bordered block. The actions
 * that apply to that artifact (download, plot editing, fullscreen) live in a
 * compact cluster docked to the block's top right corner, revealed on hover
 * or keyboard focus so the resting card stays uncluttered. Plot editing is
 * offered only for plotly artifacts; edits persist when onSaveEdit is given,
 * otherwise they are client side only.
 */
export default function ArtifactViewer({
  artifact,
  onSaveEdit = null,
  onResetEdit = null,
  canReset = false,
  siblingArtifacts = null,
  siblingIndex = 0,
  height = null,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["explainers", "common"]);
  const [downloadAnchor, setDownloadAnchor] = useState(null);
  const [editing, setEditing] = useState(false);
  const [fullscreen, setFullscreen] = useState(false);
  const [fullscreenIndex, setFullscreenIndex] = useState(siblingIndex);
  const hasSiblings = siblingArtifacts && siblingArtifacts.length > 1;

  // The parent list does not refetch after a save, so hold the edited payload
  // locally and render from it, making a save show immediately. Cleared when
  // the underlying artifact prop actually changes (e.g. a real refetch/reset).
  const [localPayload, setLocalPayload] = useState(null);
  useEffect(() => {
    setLocalPayload(null);
  }, [artifact.payload]);
  const shownArtifact =
    localPayload != null
      ? { ...artifact, payload: localPayload, overridden: true }
      : artifact;

  const fullscreenArtifact = hasSiblings
    ? siblingArtifacts[fullscreenIndex]
    : shownArtifact;

  const openFullscreen = () => {
    setFullscreenIndex(siblingIndex);
    setFullscreen(true);
  };

  const stepFullscreen = (delta) => {
    if (!hasSiblings) return;
    setFullscreenIndex(
      (fullscreenIndex + delta + siblingArtifacts.length) %
        siblingArtifacts.length,
    );
  };
  // Working copies the form editor mutates. The preview Plot renders from these
  // directly, so edits made in the form show live; the form is the single
  // source of truth, so there is no Plotly edit-event feedback loop.
  const [editData, setEditData] = useState(null);
  const [editLayout, setEditLayout] = useState(null);
  const plotWrapRef = useRef(null);
  const isPlotly = artifact.type === "plotly";

  const figure = useMemo(() => {
    if (!isPlotly) return null;
    try {
      return typeof shownArtifact.payload === "string"
        ? JSON.parse(shownArtifact.payload)
        : shownArtifact.payload;
    } catch (error) {
      console.error("Invalid plotly payload", error);
      return null;
    }
  }, [shownArtifact, isPlotly]);

  const startEdit = () => {
    if (!figure?.data) return;
    setEditData(structuredClone(figure.data));
    // An already-overridden figure keeps its saved colors; a fresh one is
    // themed so the editor starts from the current on-screen appearance.
    setEditLayout(
      shownArtifact.overridden
        ? structuredClone(figure.layout ?? {})
        : applyThemeToLayout(figure.layout, theme),
    );
    setEditing(true);
  };

  const closeEdit = () => {
    setEditing(false);
    setEditData(null);
    setEditLayout(null);
  };

  const saveEdit = async () => {
    try {
      const edited = { data: editData, layout: editLayout };
      if (onSaveEdit && editData) {
        await onSaveEdit(edited);
      }
      // Reflect the save immediately, since the parent list is not refetched.
      setLocalPayload(JSON.stringify(edited));
      closeEdit();
    } catch (error) {
      console.error("Failed to save plot edits", error);
    }
  };

  const findPlotEl = () =>
    plotWrapRef.current
      ? plotWrapRef.current.querySelector(".js-plotly-plot")
      : null;

  const actionButtonSx = {
    color: "text.secondary",
    "&:hover": { color: "text.primary" },
  };

  // Circular "glass" buttons for the fullscreen lightbox: translucent white
  // against the dark blurred overlay, regardless of the app's light/dark
  // theme (the overlay itself is always near black).
  const lightboxButtonSx = {
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
  };

  const lightboxArrowSx = {
    top: "50%",
    right: "auto",
    transform: "translateY(-50%)",
    width: 44,
    height: 44,
  };

  // Fill 75% of the viewport in the fullscreen view, minus the card's vertical
  // padding (p: 4 => 32px top + 32px bottom) so the content fits within the
  // 75vh card without producing a scrollbar.
  const fullscreenHeight =
    typeof window !== "undefined"
      ? Math.max(360, Math.round(window.innerHeight * 0.75) - 64)
      : 720;

  return (
    <Box
      ref={plotWrapRef}
      sx={{
        position: "relative",
        width: "100%",
        border: `1px solid ${theme.palette.ui.border}`,
        borderRadius: 1,
        bgcolor: theme.palette.ui.box,
        p: 3,
        "& .artifact-actions": {
          opacity: 0,
          transition: "opacity 0.15s ease",
        },
        "&:hover .artifact-actions, &:focus-within .artifact-actions": {
          opacity: 1,
        },
        "@media (hover: none)": {
          "& .artifact-actions": { opacity: 1 },
        },
      }}
    >
      {/* Action cluster, docked to the block corner and attached to this
          artifact's content. */}
      <Box
        className="artifact-actions"
        sx={{
          position: "absolute",
          top: 6,
          right: 6,
          zIndex: 3,
          display: "flex",
          gap: 0.5,
          p: 0.5,
          borderRadius: 1,
          bgcolor: alpha(theme.palette.background.paper, 0.85),
          backdropFilter: "blur(4px)",
          border: `1px solid ${theme.palette.ui.border}`,
        }}
      >
        <Tooltip title={t("explainers:button.download")}>
          <IconButton
            size="small"
            sx={actionButtonSx}
            onClick={(e) =>
              isPlotly
                ? setDownloadAnchor(e.currentTarget)
                : downloadArtifact(artifact)
            }
          >
            <DownloadIcon fontSize="small" />
          </IconButton>
        </Tooltip>
        {isPlotly && figure && (
          <Tooltip title={t("explainers:button.editPlot")}>
            <IconButton size="small" sx={actionButtonSx} onClick={startEdit}>
              <EditIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        {canReset && onResetEdit && (
          <Tooltip title={t("explainers:button.resetPlot")}>
            <IconButton
              size="small"
              sx={actionButtonSx}
              onClick={() => {
                setLocalPayload(null);
                onResetEdit();
              }}
            >
              <RestartAltIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        )}
        <Tooltip title={t("explainers:button.fullscreen")}>
          <IconButton size="small" sx={actionButtonSx} onClick={openFullscreen}>
            <FullscreenIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Box>

      <Menu
        anchorEl={downloadAnchor}
        open={Boolean(downloadAnchor)}
        onClose={() => setDownloadAnchor(null)}
      >
        <MenuItem
          onClick={() => {
            downloadArtifact(artifact, { plotEl: findPlotEl(), format: "png" });
            setDownloadAnchor(null);
          }}
        >
          {t("explainers:button.downloadPng")}
        </MenuItem>
        <MenuItem
          onClick={() => {
            downloadArtifact(artifact, { plotEl: findPlotEl(), format: "svg" });
            setDownloadAnchor(null);
          }}
        >
          {t("explainers:button.downloadSvg")}
        </MenuItem>
      </Menu>

      {/* The instance label is shown once by the parent; suppress the
          per artifact title so it is not repeated on every block. Callers
          that live in a fixed size container (an explorer card) pass an
          explicit height so the figure fits its box instead of overflowing
          it; everyone else gets the renderer's own default. */}
      <ArtifactRenderer
        artifact={{ ...shownArtifact, title: null }}
        {...(height != null && { height })}
      />

      {/* Edit dialog: a live plot preview beside the shared form layout
          editor (reused from the explorer view). The form mutates editData /
          editLayout and the preview renders from them, so edits show live. */}
      <Dialog
        open={editing}
        onClose={closeEdit}
        maxWidth={false}
        slotProps={{
          paper: {
            sx: {
              width: "90vw",
              maxWidth: "none",
              height: "85vh",
              bgcolor: "background.default",
              backgroundImage: "none",
            },
          },
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            justifyContent: "space-between",
            gap: 2,
            px: 4,
            py: 2,
            flexShrink: 0,
            bgcolor: "background.default",
          }}
        >
          <Typography variant="h6" component="div" color="text.primary">
            {t("explainers:button.editPlot")}
          </Typography>
          <IconButton onClick={closeEdit} aria-label={t("common:close")}>
            <CloseIcon />
          </IconButton>
        </Box>
        <Divider sx={{ flexShrink: 0 }} />
        <Box
          sx={{
            display: "flex",
            flexDirection: { xs: "column", md: "row" },
            flex: 1,
            minHeight: 0,
            overflow: "hidden",
          }}
        >
          {/* Live preview: reuses the explorer's plot viewer so it shows the
              same overlay icon buttons (zoom, reset, fullscreen, download). */}
          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              minHeight: 0,
              overflow: "auto",
              p: 3,
              bgcolor: "background.default",
            }}
          >
            {editData && (
              <PlotlyJsonVisualizer
                data={{ data: editData, layout: editLayout }}
                fillHeight
              />
            )}
          </Box>
          {/* Form layout/trace editor */}
          <Box
            sx={{
              width: { xs: "100%", md: "15%" },
              flexShrink: 0,
              borderLeft: { md: `1px solid ${theme.palette.ui.border}` },
              minHeight: 0,
              overflow: "hidden",
            }}
          >
            {editData && (
              <PlotLayoutForm
                data={editData}
                setData={setEditData}
                layout={editLayout}
                setLayout={setEditLayout}
                onSave={saveEdit}
                sx={{ bgcolor: "background.default" }}
              />
            )}
          </Box>
        </Box>
      </Dialog>

      {/* Fullscreen view: dark blurred lightbox overlay, rounded/shadowed
          content card, and circular glass buttons for close + prev/next. */}
      <Dialog
        open={fullscreen}
        fullScreen
        onClose={() => setFullscreen(false)}
        transitionDuration={0}
        keepMounted
        PaperProps={{
          elevation: 0,
          sx: {
            bgcolor: "rgba(0, 0, 0, 0.15)",
            backgroundImage: "none",
            backdropFilter: "blur(6px)",
            willChange: "backdrop-filter",
            boxShadow: "none",
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
            aria-label={t("explainers:button.close", {
              defaultValue: "Close",
            })}
            sx={lightboxButtonSx}
          >
            <CloseIcon sx={{ fontSize: 18 }} />
          </IconButton>

          {hasSiblings && (
            <IconButton
              onClick={() => stepFullscreen(-1)}
              aria-label="previous"
              sx={{ ...lightboxButtonSx, ...lightboxArrowSx, left: 20 }}
            >
              <ArrowBackIosNewIcon sx={{ fontSize: 22 }} />
            </IconButton>
          )}

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
            <ArtifactRenderer
              artifact={{ ...fullscreenArtifact, title: null }}
              height={fullscreenHeight}
            />
          </Box>

          {hasSiblings && (
            <IconButton
              onClick={() => stepFullscreen(1)}
              aria-label="next"
              sx={{ ...lightboxButtonSx, ...lightboxArrowSx, right: 20 }}
            >
              <ArrowForwardIosIcon sx={{ fontSize: 22 }} />
            </IconButton>
          )}
        </Box>
      </Dialog>
    </Box>
  );
}

ArtifactViewer.propTypes = {
  artifact: PropTypes.shape({
    type: PropTypes.string.isRequired,
    payload: PropTypes.any,
    title: PropTypes.string,
    role: PropTypes.string,
  }).isRequired,
  onSaveEdit: PropTypes.func,
  onResetEdit: PropTypes.func,
  canReset: PropTypes.bool,
  siblingArtifacts: PropTypes.array,
  siblingIndex: PropTypes.number,
  height: PropTypes.number,
};
