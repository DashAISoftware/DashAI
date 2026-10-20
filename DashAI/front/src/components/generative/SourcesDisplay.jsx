import React, { useEffect, useId, useRef, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { Box, Typography, Button, Stack, Tooltip } from "@mui/material";
import {
  AccountTree as AccountTreeIcon,
  Source as SourceIcon,
  ViewList as ViewListIcon,
} from "@mui/icons-material";
import TraceChunksPanel from "./RAG/TraceChunksPanel";
import { filterRenderableEntries } from "./RAG/traceUtils";
import { TRACE_VIEW_CHUNKS, TRACE_VIEW_PIPELINE } from "../../constants/rag";

/**
 * Counts the distinct documents referenced by a chunk reference map.
 *
 * Chunks repeat the same `document_id` several times, so the header badge
 * reports documents, not chunks.
 *
 * @param {object|null|undefined} references - Chunk reference map by ref key.
 * @returns {number} The number of distinct document ids.
 */
const countDocuments = (references) => {
  if (!references) return 0;
  const ids = new Set(
    Object.values(references)
      .map((ref) => ref?.document_id)
      .filter((id) => id != null),
  );
  return ids.size;
};

const toggleButtonSx = {
  fontSize: "0.75rem",
  py: 0.5,
  px: 1,
  whiteSpace: "nowrap",
};

const disabledToggleButtonSx = {
  ...toggleButtonSx,
  color: "text.disabled",
  borderColor: "divider",
  cursor: "not-allowed",
  "&:hover": { backgroundColor: "transparent" },
};

/**
 * Compact summary of the sources backing a RAG answer.
 *
 * Shows the document count and two toggle buttons that expand an inline panel
 * below the header: one for the final chunks and one for the retrieval
 * pipeline. The Chunks view is always available, so legacy answers (references
 * only, no trace) still work: the panel degrades to rendering just the
 * retrieved chunks. The Pipeline toggle is disabled when no trace is
 * renderable.
 *
 * @param {object} props
 * @param {object|null} [props.references] - Chunk reference map by ref key.
 * @param {Array|null} [props.trace] - Parsed retrieval trace entries.
 * @param {string} [props.userMessage] - The user message that produced them.
 * @param {number|string} [props.sessionId] - The session that produced them.
 * @returns {JSX.Element} The sources summary card.
 */
const SourcesDisplay = ({ references, trace, userMessage, sessionId }) => {
  const { t } = useTranslation("generative");
  const [activeView, setActiveView] = useState(null);
  const detailsId = useId();
  const pipelineHintId = useId();
  const chunksButtonRef = useRef(null);
  const pipelineButtonRef = useRef(null);
  const lastActiveViewRef = useRef(null);
  const documentCount = countDocuments(references);
  const hasPipeline = filterRenderableEntries(trace).length > 0;
  const pipelineActive = activeView === TRACE_VIEW_PIPELINE && hasPipeline;
  const chunksActive = activeView !== null && !pipelineActive;
  let pipelineHint;
  if (!hasPipeline) {
    pipelineHint = t("sourcesDisplay.noPipelineTrace");
  }

  /**
   * Opens the requested view, or closes the panel when it is already active.
   * @param {string} view - The view to toggle (chunks or pipeline).
   */
  const handleToggle = (view) => {
    if (view === TRACE_VIEW_PIPELINE && !hasPipeline) return;
    if (view === TRACE_VIEW_PIPELINE ? pipelineActive : chunksActive) {
      setActiveView(null);
      return;
    }
    setActiveView(view);
  };

  useEffect(() => {
    if (activeView) {
      lastActiveViewRef.current = pipelineActive
        ? TRACE_VIEW_PIPELINE
        : TRACE_VIEW_CHUNKS;
      return;
    }
    // The panel has unmounted; return focus to the toggle that was active.
    const lastActiveView = lastActiveViewRef.current;
    if (!lastActiveView) return;
    lastActiveViewRef.current = null;
    const button =
      lastActiveView === TRACE_VIEW_PIPELINE
        ? pipelineButtonRef.current
        : chunksButtonRef.current;
    if (button) button.focus();
  }, [activeView, pipelineActive]);

  useEffect(() => {
    if (activeView === TRACE_VIEW_PIPELINE && !hasPipeline) {
      setActiveView(TRACE_VIEW_CHUNKS);
      if (chunksButtonRef.current) chunksButtonRef.current.focus();
    }
  }, [activeView, hasPipeline]);

  /**
   * Closes the panel when Escape is pressed inside the sources card.
   * @param {React.KeyboardEvent} event - The keydown event.
   */
  const handleKeyDown = (event) => {
    if (!activeView || event.key !== "Escape") return;
    event.preventDefault();
    event.stopPropagation();
    setActiveView(null);
  };

  return (
    <Box
      onKeyDown={handleKeyDown}
      sx={{
        mt: 1,
        ml: "40px",
        maxWidth: "calc(80% - 40px)",
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        backgroundColor: "background.box",
        overflow: "hidden",
        scrollMarginTop: "8px",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          flexWrap: "wrap",
          p: 1.5,
          backgroundColor: "action.hover",
          gap: 2,
        }}
      >
        <Box
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1.5,
            minWidth: 0,
          }}
        >
          <SourceIcon fontSize="small" color="primary" sx={{ flexShrink: 0 }} />
          <Typography
            variant="body2"
            sx={{
              fontWeight: "medium",
              minWidth: 0,
              overflowWrap: "anywhere",
            }}
          >
            {t("sourcesDisplay.viewSources")}
          </Typography>
          <Box
            sx={{
              backgroundColor: "primary.main",
              color: "primary.contrastText",
              borderRadius: "10px",
              minWidth: 20,
              height: 20,
              fontSize: "0.75rem",
              fontWeight: "bold",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              px: 0.5,
              flexShrink: 0,
            }}
          >
            {documentCount}
          </Box>
        </Box>

        <Stack
          direction="row"
          spacing={1}
          role="group"
          aria-label={t("traceChunks.sectionsLabel")}
        >
          <Button
            ref={chunksButtonRef}
            size="small"
            variant={chunksActive ? "contained" : "outlined"}
            startIcon={<ViewListIcon />}
            aria-expanded={chunksActive}
            aria-controls={chunksActive ? detailsId : undefined}
            onClick={() => handleToggle(TRACE_VIEW_CHUNKS)}
            sx={toggleButtonSx}
          >
            {t("sourcesDisplay.chunks")}
          </Button>

          <Tooltip title={pipelineHint}>
            <span>
              <Button
                ref={pipelineButtonRef}
                size="small"
                variant={pipelineActive ? "contained" : "outlined"}
                startIcon={<AccountTreeIcon />}
                aria-disabled={!hasPipeline}
                aria-expanded={pipelineActive}
                aria-controls={pipelineActive ? detailsId : undefined}
                aria-describedby={!hasPipeline ? pipelineHintId : undefined}
                onClick={() => handleToggle(TRACE_VIEW_PIPELINE)}
                sx={hasPipeline ? toggleButtonSx : disabledToggleButtonSx}
              >
                {t("sourcesDisplay.pipeline")}
              </Button>
            </span>
          </Tooltip>
          {!hasPipeline && (
            <Box
              component="span"
              id={pipelineHintId}
              sx={{
                position: "absolute",
                width: 1,
                height: 1,
                overflow: "hidden",
                clip: "rect(0 0 0 0)",
                whiteSpace: "nowrap",
                m: -1,
                p: 0,
                border: 0,
              }}
            >
              {pipelineHint}
            </Box>
          )}
        </Stack>
      </Box>

      {activeView && (
        <TraceChunksPanel
          id={detailsId}
          activeView={activeView}
          onClose={() => setActiveView(null)}
          userMessage={userMessage}
          trace={trace}
          references={references}
          sessionId={sessionId}
        />
      )}
    </Box>
  );
};

SourcesDisplay.propTypes = {
  references: PropTypes.object,
  trace: PropTypes.array,
  userMessage: PropTypes.string,
  sessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};

export default SourcesDisplay;
