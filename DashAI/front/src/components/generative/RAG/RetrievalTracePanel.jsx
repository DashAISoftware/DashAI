import React, { useState } from "react";
import { useTranslation } from "react-i18next";
import { Box, Typography, Collapse, IconButton } from "@mui/material";
import {
  ExpandMore,
  ExpandLess,
  Search as SearchIcon,
} from "@mui/icons-material";

const missingChipSx = {
  display: "inline-block",
  border: 1,
  borderColor: "divider",
  borderRadius: "4px",
  px: 0.5,
  color: "text.disabled",
  fontFamily: "monospace",
  fontSize: "0.75rem",
  lineHeight: 1.4,
};

// A single trace chunk reference. It is a left-outer join key against the
// reference map: when the chunk is present we show its document info, when it
// is missing (e.g. cascade-stage candidates) we fall back to the raw ref.
const ChunkRef = ({ chunkRef, info }) => {
  const { t } = useTranslation("generative");

  if (!info) {
    return (
      <Box component="span" sx={missingChipSx}>
        {chunkRef}
      </Box>
    );
  }

  const label =
    info.page != null
      ? t("documentReferences.chunkLabelWithPage", {
          position: info.document_position,
          page: info.page,
        })
      : t("documentReferences.chunkLabel", {
          position: info.document_position,
        });

  return (
    <Typography component="span" variant="caption" color="text.secondary">
      <Box
        component="span"
        sx={{
          fontWeight: "bold",
          color: "text.primary",
          overflow: "hidden",
          textOverflow: "ellipsis",
          whiteSpace: "nowrap",
          minWidth: 0,
        }}
      >
        {info.document_name ?? chunkRef}
      </Box>
      {" · "}
      {label}
    </Typography>
  );
};

// One retriever node, rendered recursively so composite retrievers show their
// children (indented one step) inside them.
const TraceNode = ({ node, references, depth = 0 }) => {
  const { t } = useTranslation("generative");

  if (!node || typeof node !== "object") return null;

  const chunks = Array.isArray(node.chunks) ? node.chunks : [];
  const children = Array.isArray(node.children) ? node.children : [];
  const scores = Array.isArray(node.scores) ? node.scores : [];

  return (
    <Box
      sx={{
        mt: 1,
        ...(depth > 0
          ? { pl: 2, borderLeft: 1, borderColor: "divider" }
          : null),
      }}
    >
      <Box
        sx={{ display: "flex", alignItems: "center", gap: 1, flexWrap: "wrap" }}
      >
        <Typography variant="body2" sx={{ fontWeight: "bold" }}>
          {node.name}
        </Typography>
        <Typography variant="caption" color="text.secondary">
          {t("retrievalTrace.chunksLabel", { count: chunks.length })}
        </Typography>
      </Box>

      {chunks.length > 0 && (
        <Box
          sx={{ display: "flex", flexDirection: "column", gap: 0.25, mt: 0.5 }}
        >
          {chunks.map((chunkRef, index) => (
            <ChunkRef
              key={`${chunkRef}-${index}`}
              chunkRef={chunkRef}
              info={references ? references[chunkRef] : undefined}
            />
          ))}
        </Box>
      )}

      {scores.length > 0 && (
        <Box sx={{ mt: 0.5 }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: "medium" }}
          >
            {t("retrievalTrace.scoresLabel")}
          </Typography>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 0.25 }}>
            {scores.map((entry, index) => (
              <Typography
                key={`${entry?.ref}-${index}`}
                variant="caption"
                color="text.secondary"
              >
                {entry?.ref}:{" "}
                {typeof entry?.score === "number"
                  ? entry.score.toFixed(3)
                  : entry?.score}
              </Typography>
            ))}
          </Box>
        </Box>
      )}

      {children.map((child, index) => (
        <TraceNode
          key={index}
          node={child}
          references={references}
          depth={depth + 1}
        />
      ))}
    </Box>
  );
};

/**
 * Collapsible panel that shows, per query, what each retriever recovered.
 *
 * Purely presentational: the trace is the already-parsed backend payload and
 * the references map is the chunk lookup used to resolve trace refs. Returns
 * null when there is no trace to show.
 *
 * @param {object} props
 * @param {Array} props.trace - Parsed trace entries (one per query).
 * @param {object} [props.references] - Chunk reference map by ref key.
 * @param {boolean} [props.isUser=false] - Alignment side of the bubble.
 * @returns {JSX.Element|null} The panel, or null when there is no trace.
 */
const RetrievalTracePanel = ({ trace, references, isUser = false }) => {
  const { t } = useTranslation("generative");
  const [expanded, setExpanded] = useState(false);

  if (!Array.isArray(trace) || trace.length === 0) return null;

  return (
    <Box
      sx={{
        mt: 1,
        ml: isUser ? 0 : "40px",
        mr: isUser ? "40px" : 0,
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
        role="button"
        tabIndex={0}
        aria-expanded={expanded}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          p: 1.5,
          backgroundColor: "action.hover",
          cursor: "pointer",
        }}
        onClick={() => setExpanded((prev) => !prev)}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 1.5 }}>
          <SearchIcon fontSize="small" color="primary" sx={{ flexShrink: 0 }} />
          <Typography
            variant="body2"
            sx={{ fontWeight: "medium", flexShrink: 0 }}
          >
            {t("retrievalTrace.title")}
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
            {trace.length}
          </Box>
        </Box>

        <IconButton size="small" aria-label={t("retrievalTrace.title")}>
          {expanded ? <ExpandLess /> : <ExpandMore />}
        </IconButton>
      </Box>

      {/* Trace body */}
      <Collapse in={expanded} timeout="auto">
        <Box sx={{ p: 2, display: "flex", flexDirection: "column", gap: 1.5 }}>
          {trace.map((entry, index) => (
            <Box key={index}>
              <Typography variant="body2" sx={{ fontWeight: "bold" }}>
                {t("retrievalTrace.queryLabel", { index: index + 1 })}
              </Typography>
              {typeof entry?.query === "string" && entry.query ? (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ wordBreak: "break-word" }}
                >
                  {entry.query}
                </Typography>
              ) : null}
              <TraceNode node={entry?.retriever} references={references} />
            </Box>
          ))}
        </Box>
      </Collapse>
    </Box>
  );
};

export default RetrievalTracePanel;
