import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Typography, Button } from "@mui/material";
import {
  Source as SourceIcon,
  Visibility as VisibilityIcon,
} from "@mui/icons-material";
import TraceChunksModal from "./RAG/TraceChunksModal";

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

/**
 * Compact summary of the sources backing a RAG answer.
 *
 * Shows the document count and a single button that opens the combined
 * trace-and-chunks modal. The modal is opened regardless of whether a trace is
 * present, so legacy answers (references only, no trace) still work: the modal
 * degrades to rendering just the retrieved chunks.
 *
 * @param {object} props
 * @param {object|null} [props.references] - Chunk reference map by ref key.
 * @param {Array|null} [props.trace] - Parsed retrieval trace entries.
 * @param {string} [props.userMessage] - The user message that produced them.
 * @returns {JSX.Element} The sources summary card.
 */
const SourcesDisplay = ({ references, trace, userMessage }) => {
  const { t } = useTranslation("generative");
  const [modalOpen, setModalOpen] = useState(false);
  const documentCount = countDocuments(references);

  return (
    <Box
      sx={{
        mt: 1,
        ml: "40px",
        maxWidth: "calc(80% - 40px)",
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        backgroundColor: "background.box",
        overflow: "hidden",
      }}
    >
      {/* Header */}
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 1.5,
          backgroundColor: "action.hover",
          gap: 2,
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <SourceIcon fontSize="small" color="primary" sx={{ flexShrink: 0 }} />
          <Typography
            variant="body2"
            sx={{ fontWeight: "medium", flexShrink: 0 }}
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

        <Button
          size="small"
          variant="outlined"
          startIcon={<VisibilityIcon />}
          onClick={() => setModalOpen(true)}
          sx={{
            fontSize: "0.75rem",
            py: 0.5,
            px: 1,
            whiteSpace: "nowrap",
            minWidth: "140px",
            flexShrink: 0,
          }}
        >
          {t("sourcesDisplay.viewChunks")}
        </Button>
      </Box>

      <TraceChunksModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        userMessage={userMessage}
        trace={trace}
        references={references}
      />
    </Box>
  );
};

export default SourcesDisplay;
