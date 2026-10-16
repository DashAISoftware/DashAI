import { useState, useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  Dialog,
  DialogContent,
  DialogTitle,
  IconButton,
  Paper,
  Stack,
  Tooltip,
  Typography,
} from "@mui/material";
import {
  Article as ArticleIcon,
  Close as CloseIcon,
  ContentCopy as CopyIcon,
  ExpandMore as ExpandMoreIcon,
  OpenInNew as OpenInNewIcon,
} from "@mui/icons-material";
import RetrieverTraceTree from "./RetrieverTraceTree";
import {
  isPlainObject,
  isQueryTransformed,
  filterRenderableEntries,
  groupReferencesByDocument,
  getDocumentTitle,
  resolveChunkLabel,
  collectTraceStats,
  computeDiscardedRefs,
  computeProvenance,
} from "./traceUtils";

// Chunk bodies longer than this many characters collapse behind a toggle.
const TEXT_CLAMP_LENGTH = 480;
// Number of rendered lines before a clamped chunk body is cut off.
const TEXT_CLAMP_LINES = 8;

/**
 * Builds the localised provenance line for one chunk ("Found by A (query 1)").
 * @param {Array<{queryIndex: number, names: string[]}>} [entries] - Provenance.
 * @param {Function} t - i18n translate function.
 * @returns {string|null} The provenance sentence, or null when there is none.
 */
function buildProvenanceText(entries, t) {
  const labels = (entries ?? []).flatMap(({ queryIndex, names }) =>
    names.map(
      (name) =>
        `${name} (${t("traceChunks.foundByQuery", { index: queryIndex })})`,
    ),
  );
  if (labels.length === 0) return null;
  return t("traceChunks.foundBy", { retrievers: labels.join(", ") });
}

/**
 * The user message rendered as a quiet, left-bordered quote.
 * @param {object} props
 * @param {string} props.userMessage - The original user message.
 * @returns {JSX.Element} The quote block.
 */
function QuestionQuote({ userMessage }) {
  return (
    <Box
      data-testid="user-message-quote"
      sx={{
        borderLeft: 3,
        borderColor: "primary.main",
        pl: 1.5,
        color: "text.secondary",
      }}
    >
      <Typography
        variant="body1"
        sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
      >
        {userMessage}
      </Typography>
    </Box>
  );
}

QuestionQuote.propTypes = {
  userMessage: PropTypes.string.isRequired,
};

/**
 * One-line summary of how the retrieved candidates relate to the answer.
 * @param {object} props
 * @param {boolean} props.transformed - Whether the query was rewritten.
 * @param {number} props.queryCount - Number of queries used.
 * @param {number} props.kept - Number of reference chunks in the answer.
 * @param {number} props.total - Number of distinct retrieved candidates.
 * @returns {JSX.Element} The story strip.
 */
function StoryStrip({ transformed, queryCount, kept, total }) {
  const { t } = useTranslation("generative");
  let intro;
  if (transformed) {
    intro = t("traceChunks.storyRewritten", { count: queryCount });
  } else {
    intro = t("traceChunks.storyDirect");
  }
  let counts;
  if (kept < total) {
    counts = t("traceChunks.storyKept", { kept, total });
  } else {
    counts = t("traceChunks.storyKeptAll", { count: kept });
  }
  return (
    <Typography
      data-testid="story-strip"
      variant="body2"
      color="text.secondary"
    >
      {intro} {counts}
    </Typography>
  );
}

StoryStrip.propTypes = {
  transformed: PropTypes.bool.isRequired,
  queryCount: PropTypes.number.isRequired,
  kept: PropTypes.number.isRequired,
  total: PropTypes.number.isRequired,
};

/**
 * The header row of a chunk card: label, provenance and copy action.
 * @param {object} props
 * @param {string} props.label - The localised chunk label.
 * @param {string|null} props.provenanceText - The localised provenance line.
 * @param {string} props.chunkText - The raw chunk text to copy.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @returns {JSX.Element} The header row.
 */
function ChunkCardHeader({ label, provenanceText, chunkText, onCopy }) {
  const { t } = useTranslation(["generative", "common"]);
  return (
    <Stack
      direction="row"
      alignItems="flex-start"
      justifyContent="space-between"
      spacing={1}
      sx={{ mb: 1 }}
    >
      <Typography variant="subtitle2">{label}</Typography>
      <Stack
        direction="row"
        alignItems="center"
        spacing={1}
        sx={{ minWidth: 0 }}
      >
        {provenanceText && (
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ textAlign: "right", wordBreak: "break-word" }}
          >
            {provenanceText}
          </Typography>
        )}
        <Tooltip title={t("common:copy", "Copy")}>
          <IconButton
            size="small"
            aria-label={t("common:copy", "Copy")}
            onClick={(event) => {
              event.stopPropagation();
              onCopy(chunkText);
            }}
            sx={{
              color: "text.secondary",
              flexShrink: 0,
              "&:hover": {
                color: "primary.main",
                backgroundColor: "action.hover",
              },
            }}
          >
            <CopyIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </Stack>
    </Stack>
  );
}

ChunkCardHeader.propTypes = {
  label: PropTypes.string.isRequired,
  provenanceText: PropTypes.string,
  chunkText: PropTypes.string,
  onCopy: PropTypes.func.isRequired,
};

/**
 * The show-more/show-less label of a clamped chunk body.
 * @param {object} props
 * @param {boolean} props.expanded - Whether the body is currently expanded.
 * @returns {JSX.Element} The label text.
 */
function ToggleLabel({ expanded }) {
  const { t } = useTranslation("generative");
  if (expanded) {
    return <>{t("traceChunks.showLess")}</>;
  }
  return <>{t("traceChunks.showMore")}</>;
}

ToggleLabel.propTypes = {
  expanded: PropTypes.bool.isRequired,
};

/**
 * A chunk body that clamps long text to a fixed number of lines behind a
 * per-card "Show more"/"Show less" toggle.
 * @param {object} props
 * @param {string} props.text - The raw chunk text.
 * @returns {JSX.Element|null} The body and its optional toggle, or null when
 *   the text is missing.
 */
function ChunkText({ text }) {
  const [expanded, setExpanded] = useState(false);
  let body = null;
  if (typeof text === "string") {
    body = text.replace(/\\n/g, "\n");
  }
  const exceeds = body !== null && body.length > TEXT_CLAMP_LENGTH;
  const clamped = exceeds && !expanded;
  if (body === null) return null;
  return (
    <>
      <Typography
        variant="body2"
        sx={{
          lineHeight: 1.6,
          whiteSpace: "pre-wrap",
          wordBreak: "break-word",
          display: clamped ? "-webkit-box" : "block",
          WebkitLineClamp: clamped ? TEXT_CLAMP_LINES : "unset",
          WebkitBoxOrient: "vertical",
          overflow: clamped ? "hidden" : "visible",
        }}
      >
        {body}
      </Typography>
      {exceeds && (
        <Button
          size="small"
          variant="text"
          onClick={(event) => {
            event.stopPropagation();
            setExpanded((value) => !value);
          }}
          sx={{
            mt: 0.5,
            p: 0,
            minWidth: 0,
            textTransform: "none",
            fontWeight: 400,
          }}
        >
          <ToggleLabel expanded={expanded} />
        </Button>
      )}
    </>
  );
}

ChunkText.propTypes = {
  text: PropTypes.string,
};

/**
 * A single final chunk card: label + provenance + copy, clamped body, and a
 * keyboard-operable highlight target.
 * @param {object} props
 * @param {object} props.chunk - A chunk with its raw `ref` plus reference data.
 * @param {boolean} props.isHighlighted - Whether this card is highlighted.
 * @param {React.RefObject} props.highlightedCardRef - Ref set when highlighted.
 * @param {Map} props.provenanceMap - Ref → per-query deepest retriever names.
 * @param {Function} props.onSelect - Highlights this chunk's ref.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @returns {JSX.Element} The chunk card.
 */
function ChunkCard({
  chunk,
  isHighlighted,
  highlightedCardRef,
  provenanceMap,
  onSelect,
  onCopy,
}) {
  const { t } = useTranslation("generative");
  const label = resolveChunkLabel(chunk, t);
  const provenanceText = buildProvenanceText(provenanceMap.get(chunk.ref), t);

  const handleKeyDown = (event) => {
    if (event.target !== event.currentTarget) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onSelect(chunk.ref);
  };

  /**
   * Highlights the card, unless the user is text-selecting inside it: the
   * mouseup would otherwise fire a click and jump the highlight.
   * @param {React.MouseEvent} event - The click event.
   */
  const handleClick = (event) => {
    const selection =
      typeof window.getSelection === "function" ? window.getSelection() : null;
    if (selection && selection.toString().length > 0) return;
    onSelect(chunk.ref);
  };

  return (
    <Paper
      ref={isHighlighted ? highlightedCardRef : null}
      data-testid={
        isHighlighted ? "highlighted-chunk-card" : `chunk-card-${chunk.ref}`
      }
      elevation={0}
      role="button"
      aria-pressed={isHighlighted}
      tabIndex={0}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      sx={{
        p: 2,
        cursor: "pointer",
        border: isHighlighted ? 2 : 1,
        borderColor: isHighlighted ? "primary.main" : "divider",
        bgcolor: isHighlighted ? "action.selected" : "background.paper",
        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: 2,
        },
        ...(isHighlighted
          ? {}
          : { "&:hover": { backgroundColor: "action.hover" } }),
      }}
    >
      <ChunkCardHeader
        label={label}
        provenanceText={provenanceText}
        chunkText={chunk.text}
        onCopy={onCopy}
      />
      <ChunkText text={chunk.text} />
    </Paper>
  );
}

ChunkCard.propTypes = {
  chunk: PropTypes.object.isRequired,
  isHighlighted: PropTypes.bool.isRequired,
  highlightedCardRef: PropTypes.object.isRequired,
  provenanceMap: PropTypes.object.isRequired,
  onSelect: PropTypes.func.isRequired,
  onCopy: PropTypes.func.isRequired,
};

/**
 * One document's chunk cards with a header, count and "Open document" action.
 * @param {object} props
 * @param {{docId: *, chunks: Array<object>}} props.group - The document group.
 * @param {string|null} props.highlightedRef - The currently highlighted ref.
 * @param {React.RefObject} props.highlightedCardRef - Ref set when highlighted.
 * @param {Map} props.provenanceMap - Ref → per-query deepest retriever names.
 * @param {Function} props.onSelect - Highlights a chunk ref.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @param {Function} props.onOpenDocument - Opens a document by id.
 * @returns {JSX.Element} The document group.
 */
function DocumentGroup({
  group,
  highlightedRef,
  highlightedCardRef,
  provenanceMap,
  onSelect,
  onCopy,
  onOpenDocument,
}) {
  const { t } = useTranslation("generative");
  const title = getDocumentTitle(group.chunks[0], group.docId, t);
  return (
    <Box data-testid={`doc-group-${group.docId}`} sx={{ mb: 2 }}>
      <Stack
        direction="row"
        alignItems="center"
        justifyContent="space-between"
        spacing={1}
        sx={{ mb: 1 }}
      >
        <Stack
          direction="row"
          alignItems="center"
          spacing={1}
          sx={{ minWidth: 0 }}
        >
          <ArticleIcon color="primary" sx={{ fontSize: 18, flexShrink: 0 }} />
          <Tooltip title={title}>
            <Typography variant="subtitle1" noWrap sx={{ fontWeight: 600 }}>
              {title}
            </Typography>
          </Tooltip>
        </Stack>
        <Stack direction="row" alignItems="center" spacing={1}>
          <Typography variant="caption" color="text.secondary">
            {t("traceChunks.chunksLabel", { count: group.chunks.length })}
          </Typography>
          <Tooltip title={t("traceChunks.openDocument")}>
            <IconButton
              size="small"
              aria-label={t("traceChunks.openDocument")}
              onClick={() => onOpenDocument(group.docId)}
            >
              <OpenInNewIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
      </Stack>
      <Stack spacing={1}>
        {group.chunks.map((chunk) => (
          <ChunkCard
            key={chunk.ref}
            chunk={chunk}
            isHighlighted={chunk.ref === highlightedRef}
            highlightedCardRef={highlightedCardRef}
            provenanceMap={provenanceMap}
            onSelect={onSelect}
            onCopy={onCopy}
          />
        ))}
      </Stack>
    </Box>
  );
}

DocumentGroup.propTypes = {
  group: PropTypes.object.isRequired,
  highlightedRef: PropTypes.string,
  highlightedCardRef: PropTypes.object.isRequired,
  provenanceMap: PropTypes.object.isRequired,
  onSelect: PropTypes.func.isRequired,
  onCopy: PropTypes.func.isRequired,
  onOpenDocument: PropTypes.func.isRequired,
};

/**
 * The answer's evidence: a heading with counts and the chunk groups.
 * @param {object} props
 * @param {Array<object>} props.groups - Reference chunks grouped by document.
 * @param {number} props.totalChunks - Total number of reference chunks.
 * @param {string|null} props.highlightedRef - The currently highlighted ref.
 * @param {React.RefObject} props.highlightedCardRef - Ref set when highlighted.
 * @param {Map} props.provenanceMap - Ref → per-query deepest retriever names.
 * @param {Function} props.onSelect - Highlights a chunk ref.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @param {Function} props.onOpenDocument - Opens a document by id.
 * @returns {JSX.Element} The received-chunks section.
 */
function ChunksSection({
  groups,
  totalChunks,
  highlightedRef,
  highlightedCardRef,
  provenanceMap,
  onSelect,
  onCopy,
  onOpenDocument,
}) {
  const { t } = useTranslation("generative");
  return (
    <Box>
      <Stack
        direction="row"
        alignItems="baseline"
        justifyContent="space-between"
        spacing={1}
        sx={{ mb: 1.5 }}
      >
        <Typography
          variant="subtitle1"
          sx={{ fontWeight: 600 }}
          data-testid="received-title"
        >
          {t("traceChunks.receivedTitle")}
        </Typography>
        <Typography
          variant="caption"
          color="text.secondary"
          data-testid="received-count"
        >
          {t("traceChunks.receivedCount", {
            count: totalChunks,
            chunks: totalChunks,
            documents: groups.length,
          })}
        </Typography>
      </Stack>
      {groups.map((group) => (
        <DocumentGroup
          key={group.docId}
          group={group}
          highlightedRef={highlightedRef}
          highlightedCardRef={highlightedCardRef}
          provenanceMap={provenanceMap}
          onSelect={onSelect}
          onCopy={onCopy}
          onOpenDocument={onOpenDocument}
        />
      ))}
    </Box>
  );
}

ChunksSection.propTypes = {
  groups: PropTypes.array.isRequired,
  totalChunks: PropTypes.number.isRequired,
  highlightedRef: PropTypes.string,
  highlightedCardRef: PropTypes.object.isRequired,
  provenanceMap: PropTypes.object.isRequired,
  onSelect: PropTypes.func.isRequired,
  onCopy: PropTypes.func.isRequired,
  onOpenDocument: PropTypes.func.isRequired,
};

/**
 * A read-only row summarising one query and its candidate count.
 * @param {object} props
 * @param {object} props.entry - A renderable trace entry.
 * @param {number} props.index - Zero-based query index.
 * @param {number} props.count - The query's recursive candidate count.
 * @returns {JSX.Element} The query summary row.
 */
function QuerySummaryRow({ entry, index, count }) {
  const { t } = useTranslation("generative");
  return (
    <Stack direction="row" alignItems="flex-start" spacing={1} sx={{ mb: 0.5 }}>
      <Chip
        size="small"
        variant="outlined"
        label={t("traceChunks.queryTooltip", { index: index + 1 })}
        sx={{
          borderColor: "accent.purple",
          color: "accent.purple",
          flexShrink: 0,
        }}
      />
      {typeof entry?.query === "string" && entry.query.length > 0 && (
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{ wordBreak: "break-word", pt: 0.25 }}
        >
          "{entry.query}"
        </Typography>
      )}
      <Typography
        variant="caption"
        color="text.secondary"
        sx={{ flexShrink: 0, pt: 0.5, ml: "auto" }}
      >
        {t("traceChunks.queryCandidates", { count })}
      </Typography>
    </Stack>
  );
}

QuerySummaryRow.propTypes = {
  entry: PropTypes.object.isRequired,
  index: PropTypes.number.isRequired,
  count: PropTypes.number.isRequired,
};

/**
 * The query-selector chips ("All" first, then one per query when multiple).
 * @param {object} props
 * @param {Array<object>} props.entries - Renderable trace entries.
 * @param {number|null} props.selectedQuery - Active index, or null for "All".
 * @param {Function} props.onSelect - Selects a query index (or null for All).
 * @returns {JSX.Element} The selector chips.
 */
function QuerySelectorChips({ entries, selectedQuery, onSelect }) {
  const { t } = useTranslation("generative");
  return (
    <Box
      data-testid="query-selector"
      sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 1.5 }}
    >
      {entries.length > 1 && (
        <Chip
          data-testid="query-chip"
          size="small"
          label={t("traceChunks.allQueriesChip")}
          color={selectedQuery === null ? "primary" : "default"}
          variant={selectedQuery === null ? "filled" : "outlined"}
          aria-pressed={selectedQuery === null}
          onClick={() => onSelect(null)}
        />
      )}
      {entries.map((entry, index) => (
        <Tooltip
          key={index}
          title={typeof entry?.query === "string" ? entry.query : undefined}
        >
          <Chip
            data-testid="query-chip"
            size="small"
            label={t("traceChunks.queryTooltip", { index: index + 1 })}
            color={selectedQuery === index ? "primary" : "default"}
            variant={selectedQuery === index ? "filled" : "outlined"}
            aria-pressed={selectedQuery === index}
            onClick={() => onSelect(index)}
          />
        </Tooltip>
      ))}
    </Box>
  );
}

QuerySelectorChips.propTypes = {
  entries: PropTypes.array.isRequired,
  selectedQuery: PropTypes.number,
  onSelect: PropTypes.func.isRequired,
};

/**
 * The recessed box holding one query's retriever tree, or all of them stacked
 * under bold "Query N" mini-headings when "All" is active.
 * @param {object} props
 * @param {Array<object>} props.entries - Renderable trace entries.
 * @param {number|null} props.selectedQuery - Active index, or null for "All".
 * @param {object|null} props.selectedEntry - The selected entry, if a specific query is active.
 * @param {object|null} props.references - Chunk reference map by ref key.
 * @param {Function} props.onChunkClick - Called with a clicked chunk's ref.
 * @returns {JSX.Element} The trace-tree box.
 */
function TraceTrees({
  entries,
  selectedQuery,
  selectedEntry,
  references,
  onChunkClick,
}) {
  const { t } = useTranslation("generative");
  /**
   * Renders one query's retriever tree, or stacks them under "Query N"
   * mini-headings when "All" is active.
   * @param {object} entry - A renderable trace entry.
   * @param {number} index - Zero-based query index.
   * @param {boolean} isLast - Whether no bottom margin should be added.
   * @returns {JSX.Element} The tree block.
   */
  const renderTree = (entry, index, isLast) => (
    <Box key={index} sx={{ mb: isLast ? 0 : 2 }}>
      <Typography variant="body2" sx={{ fontWeight: "bold", mb: 0.5 }}>
        {t("traceChunks.queryTooltip", { index: index + 1 })}
      </Typography>
      <RetrieverTraceTree
        node={entry.retriever}
        references={references}
        onChunkClick={onChunkClick}
      />
    </Box>
  );
  return (
    <Box
      data-testid="trace-tree"
      sx={{
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        p: 2,
        backgroundColor: "background.box",
        overflowX: "auto",
      }}
    >
      {selectedQuery === null
        ? entries.map((entry, index) =>
            renderTree(entry, index, index === entries.length - 1),
          )
        : selectedEntry && renderTree(selectedEntry, selectedQuery, true)}
    </Box>
  );
}

TraceTrees.propTypes = {
  entries: PropTypes.array.isRequired,
  selectedQuery: PropTypes.number,
  selectedEntry: PropTypes.object,
  references: PropTypes.object,
  onChunkClick: PropTypes.func.isRequired,
};

/**
 * The discarded candidates, as muted mono-font clickable chips.
 * @param {object} props
 * @param {string[]} props.refs - The discarded refs, in order.
 * @param {Function} props.onDiscardedClick - Called with a discarded ref.
 * @returns {JSX.Element|null} The block, or null when nothing was discarded.
 */
function DiscardedBlock({ refs, onDiscardedClick }) {
  const { t } = useTranslation("generative");
  if (refs.length === 0) return null;
  return (
    <Box sx={{ mt: 2 }}>
      <Typography
        variant="body2"
        color="text.secondary"
        sx={{ fontWeight: "medium" }}
      >
        {t("traceChunks.discardedTitle")}
      </Typography>
      <Typography variant="caption" color="text.secondary">
        {t("traceChunks.discardedCaption")}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5, mt: 1 }}>
        {refs.map((ref) => (
          <Box
            key={ref}
            data-testid={`discarded-chip-${ref}`}
            role="button"
            tabIndex={0}
            onClick={() => onDiscardedClick(ref)}
            onKeyDown={(event) => {
              if (event.key !== "Enter" && event.key !== " ") return;
              event.preventDefault();
              onDiscardedClick(ref);
            }}
            sx={(theme) => ({
              ...theme.typography.code,
              border: 1,
              borderColor: "divider",
              borderRadius: "4px",
              px: 0.5,
              color: "text.secondary",
              cursor: "pointer",
              "&:focus-visible": {
                outline: "2px solid",
                outlineColor: "primary.main",
                outlineOffset: 2,
              },
            })}
          >
            {ref}
          </Box>
        ))}
      </Box>
    </Box>
  );
}

DiscardedBlock.propTypes = {
  refs: PropTypes.array.isRequired,
  onDiscardedClick: PropTypes.func.isRequired,
};

/**
 * The per-query summary rows shown when a transformation ran.
 * @param {object} props
 * @param {Array<object>} props.entries - Renderable trace entries.
 * @param {Array<{count: number}>} props.perQuery - Per-query candidate stats.
 * @returns {JSX.Element} The summary row list.
 */
function QuerySummaryList({ entries, perQuery }) {
  return (
    <Box sx={{ mb: 1.5 }}>
      {entries.map((entry, index) => (
        <QuerySummaryRow
          key={index}
          entry={entry}
          index={index}
          count={perQuery[index]?.count ?? 0}
        />
      ))}
    </Box>
  );
}

QuerySummaryList.propTypes = {
  entries: PropTypes.array.isRequired,
  perQuery: PropTypes.array.isRequired,
};

/**
 * The quoted text of the currently selected query.
 * @param {object} props
 * @param {object} props.entry - The selected trace entry.
 * @returns {JSX.Element} The quoted query.
 */
function SelectedQueryText({ entry }) {
  return (
    <Typography
      variant="body1"
      color="text.secondary"
      data-testid="selected-query-text"
      sx={{ mb: 1, wordBreak: "break-word" }}
    >
      "{entry.query}"
    </Typography>
  );
}

SelectedQueryText.propTypes = {
  entry: PropTypes.object.isRequired,
};

/**
 * The teaching panel: per-query summary, selector and trees, discarded refs.
 * @param {object} props
 * @param {Array<object>} props.entries - Renderable trace entries.
 * @param {Array<{count: number}>} props.perQuery - Per-query candidate stats.
 * @param {string[]} props.discardedRefs - Refs that never reached the answer.
 * @param {boolean} props.transformed - Whether the query was rewritten.
 * @param {number|null} props.selectedQuery - Active index, or null for "All".
 * @param {object|null} props.selectedEntry - The selected entry, if any.
 * @param {object|null} props.references - Chunk reference map by ref key.
 * @param {Function} props.onSelectQuery - Selects a query index (or null).
 * @param {Function} props.onChunkClick - Called with a clicked chunk's ref.
 * @returns {JSX.Element} The method accordion.
 */
function MethodPanel({
  entries,
  perQuery,
  discardedRefs,
  transformed,
  selectedQuery,
  selectedEntry,
  references,
  onSelectQuery,
  onChunkClick,
}) {
  const { t } = useTranslation("generative");
  const showSelectedText =
    transformed &&
    selectedQuery !== null &&
    Boolean(selectedEntry) &&
    typeof selectedEntry.query === "string" &&
    selectedEntry.query.length > 0;
  return (
    <Accordion
      data-testid="method-panel"
      defaultExpanded={transformed}
      disableGutters
      elevation={0}
      sx={{
        border: 1,
        borderColor: "divider",
        borderRadius: 1,
        "&:before": { display: "none" },
        backgroundImage: "none",
      }}
    >
      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
        <Typography variant="subtitle1" sx={{ fontWeight: 600 }}>
          {t("traceChunks.methodTitle")}
        </Typography>
      </AccordionSummary>
      <AccordionDetails
        sx={{
          backgroundColor: "background.box",
          borderTop: 1,
          borderColor: "divider",
        }}
      >
        {transformed && (
          <QuerySummaryList entries={entries} perQuery={perQuery} />
        )}

        {transformed && (
          <QuerySelectorChips
            entries={entries}
            selectedQuery={selectedQuery}
            onSelect={onSelectQuery}
          />
        )}

        {showSelectedText && <SelectedQueryText entry={selectedEntry} />}

        <TraceTrees
          entries={entries}
          selectedQuery={selectedQuery}
          selectedEntry={selectedEntry}
          references={references}
          onChunkClick={onChunkClick}
        />
        <DiscardedBlock refs={discardedRefs} onDiscardedClick={onChunkClick} />
      </AccordionDetails>
    </Accordion>
  );
}

MethodPanel.propTypes = {
  entries: PropTypes.array.isRequired,
  perQuery: PropTypes.array.isRequired,
  discardedRefs: PropTypes.array.isRequired,
  transformed: PropTypes.bool.isRequired,
  selectedQuery: PropTypes.number,
  selectedEntry: PropTypes.object,
  references: PropTypes.object,
  onSelectQuery: PropTypes.func.isRequired,
  onChunkClick: PropTypes.func.isRequired,
};

/**
 * Combined trace + final-chunks modal for a RAG response.
 *
 * The body is a single scrolling column: a quiet quote of the user message, a
 * one-line story strip of how the retrieval unfolded, the final chunks grouped
 * by document (each attributed to the deepest retriever that found it), and a
 * collapsible method panel that teaches the selection with the per-query
 * retriever trees. Clicking a tree chunk or a chunk card resolves it against the
 * references map: survivors highlight their card, discarded chunks warn instead.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is visible.
 * @param {Function} props.onClose - Closes the dialog.
 * @param {string} [props.userMessage] - The original user message.
 * @param {Array|null} [props.trace] - Per-query retriever trace, if any.
 * @param {object|null} [props.references] - Final chunk reference map.
 * @returns {JSX.Element} The dialog.
 */
const TraceChunksModal = ({
  open,
  onClose,
  userMessage,
  trace,
  references,
}) => {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const [selectedQuery, setSelectedQuery] = useState(0);
  const [highlightedRef, setHighlightedRef] = useState(null);
  const highlightedCardRef = useRef(null);
  // Tracks the previous `open` value so the state reset fires only on the
  // close→open transition: while a chat process is polling, the parent rebuilds
  // trace/references objects on every poll, and re-resetting on identity change
  // would visibly wipe the user's query selection and highlight mid-read.
  const prevOpenRef = useRef(false);

  useEffect(() => {
    if (open && !prevOpenRef.current) {
      const renderable = filterRenderableEntries(trace);
      setSelectedQuery(renderable.length > 1 ? null : 0);
      setHighlightedRef(null);
    }
    prevOpenRef.current = open;
  }, [open, trace, references]);

  useEffect(() => {
    const el = highlightedCardRef.current;
    if (el && typeof el.scrollIntoView === "function") {
      const reduceMotion =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      el.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
        block: "nearest",
      });
    }
  }, [highlightedRef]);

  const entries = filterRenderableEntries(trace);
  const groups = groupReferencesByDocument(references);
  const hasReferences = groups.length > 0;
  const transformed = isQueryTransformed(entries, userMessage);
  const { candidates, perQuery } = collectTraceStats(entries);
  const discardedRefs = computeDiscardedRefs(entries, references);
  const provenanceMap = computeProvenance(entries);
  // Kept counts only the validated chunks that actually render, and the
  // candidate total never reports fewer than kept, so a corrupt or legacy
  // trace can never make the strip claim more survivors than it shows.
  const kept = groups.reduce((sum, group) => sum + group.chunks.length, 0);
  const total = Math.max(candidates.length, kept);
  // A trace replaced mid-read (the chat polls and rebuilds props) can shrink
  // below the stored selection; fall back to the "All" view instead of an
  // empty tree panel.
  let effectiveSelectedQuery = selectedQuery;
  if (
    effectiveSelectedQuery !== null &&
    (effectiveSelectedQuery < 0 || effectiveSelectedQuery >= entries.length)
  ) {
    effectiveSelectedQuery = null;
  }
  const selectedEntry =
    effectiveSelectedQuery === null ? null : entries[effectiveSelectedQuery];

  /**
   * Highlights the matching final chunk, or warns when the trace chunk never
   * reached the end of the pipeline.
   * @param {string} chunkRef - The clicked raw reference key.
   */
  const handleChunkClick = useCallback(
    (chunkRef) => {
      if (isPlainObject(references) && references[chunkRef]) {
        setHighlightedRef(chunkRef);
      } else {
        enqueueSnackbar(t("generative:traceChunks.discarded"), {
          variant: "warning",
        });
      }
    },
    [references, enqueueSnackbar, t],
  );

  /**
   * Copies a chunk's text to the clipboard with escaped newlines restored and
   * confirms the outcome: clipboard denial in a webview is otherwise silent.
   * @param {string} chunkText - The raw chunk text.
   */
  const handleCopyChunk = useCallback(
    async (chunkText) => {
      if (typeof chunkText !== "string") return;
      try {
        await navigator.clipboard.writeText(chunkText.replace(/\\n/g, "\n"));
        enqueueSnackbar(t("common:copied"), { variant: "success" });
      } catch {
        enqueueSnackbar(t("common:copy"), { variant: "warning" });
      }
    },
    [enqueueSnackbar, t],
  );

  /**
   * Navigates to a document page and closes the dialog.
   * @param {number|string} docId - The document identifier.
   */
  const handleOpenDocument = useCallback(
    (docId) => {
      if (docId == null) return;
      navigate(`/app/data/documents/${docId}`);
      onClose();
    },
    [navigate, onClose],
  );

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      aria-labelledby="trace-chunks-title"
      // MUI v7: PaperProps is deprecated in favour of slotProps.paper.
      slotProps={{ paper: { sx: { maxHeight: "85vh" } } }}
    >
      <DialogTitle
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 1,
        }}
      >
        <Typography
          variant="h6"
          component="div"
          id="trace-chunks-title"
          data-testid="trace-chunks-title"
        >
          {t("generative:traceChunks.title")}
        </Typography>
        <Tooltip title={t("common:close")}>
          <IconButton
            size="small"
            onClick={onClose}
            aria-label={t("common:close")}
          >
            <CloseIcon fontSize="small" />
          </IconButton>
        </Tooltip>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Stack spacing={2}>
          {typeof userMessage === "string" && userMessage.length > 0 && (
            <QuestionQuote userMessage={userMessage} />
          )}

          {entries.length > 0 && hasReferences && (
            <StoryStrip
              transformed={transformed}
              queryCount={entries.length}
              kept={kept}
              total={total}
            />
          )}

          <Box data-testid="final-chunks-panel">
            {hasReferences ? (
              <ChunksSection
                groups={groups}
                totalChunks={kept}
                highlightedRef={highlightedRef}
                highlightedCardRef={highlightedCardRef}
                provenanceMap={provenanceMap}
                onSelect={setHighlightedRef}
                onCopy={handleCopyChunk}
                onOpenDocument={handleOpenDocument}
              />
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t("generative:traceChunks.emptyState")}
              </Typography>
            )}
          </Box>

          {entries.length > 0 && (
            <MethodPanel
              entries={entries}
              perQuery={perQuery}
              discardedRefs={discardedRefs}
              transformed={transformed}
              selectedQuery={effectiveSelectedQuery}
              selectedEntry={selectedEntry}
              references={references}
              onSelectQuery={setSelectedQuery}
              onChunkClick={handleChunkClick}
            />
          )}
        </Stack>
      </DialogContent>
    </Dialog>
  );
};

TraceChunksModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  userMessage: PropTypes.string,
  trace: PropTypes.any,
  references: PropTypes.object,
};

export default TraceChunksModal;
