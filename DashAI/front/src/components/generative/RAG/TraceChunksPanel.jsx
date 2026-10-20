import { useState, useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import {
  Box,
  Button,
  Chip,
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
  OpenInNew as OpenInNewIcon,
} from "@mui/icons-material";
import RetrieverTraceTree from "./RetrieverTraceTree";
import {
  getRetrievalParadigm,
  getSessionConfiguration,
} from "../../../api/rag";
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
import { TRACE_VIEW_CHUNKS, TRACE_VIEW_PIPELINE } from "../../../constants/rag";

// Cached retriever component map, keyed by class name. Used as a fallback for
// traces recorded before the trace payload carried description/representation.
let retrieverComponentsPromise = null;
// Resolved map retained across panel mounts so a reopen never flashes the view
// without descriptions or representations.
let retrieverComponentsCache = null;

/**
 * Load (once) the registered retriever components keyed by class name.
 *
 * Legacy traces only carry the retriever class name. The component registry is
 * the only remaining source for their description, so the trace view resolves
 * it once and shares the result across panel mounts.
 *
 * @returns {Promise<Record<string, object>>} Map of class name to component.
 */
function loadRetrieverComponents() {
  if (retrieverComponentsCache) {
    return Promise.resolve(retrieverComponentsCache);
  }
  if (!retrieverComponentsPromise) {
    retrieverComponentsPromise = getRetrievalParadigm()
      .then((components) => {
        const map = {};
        for (const component of components || []) {
          if (component?.name) map[component.name] = component;
        }
        retrieverComponentsCache = map;
        return map;
      })
      .catch((error) => {
        // Allow a later panel mount to retry after a transient failure.
        retrieverComponentsPromise = null;
        console.warn("Failed to load retriever components:", error);
        return {};
      });
  }
  return retrieverComponentsPromise;
}

/**
 * Convert the resolved `retriever_model` section into a `{component, params}`
 * tree. The API describes parameters as `{name, value}` pairs; the
 * representation resolver expects the raw parameter mapping.
 *
 * @param {object|null|undefined} section - The resolved retriever section.
 * @returns {{component: string, params: object}|null} The raw config tree.
 */
function toRetrieverConfig(section) {
  if (!section?.component) return null;
  const params = {};
  for (const param of section.params || []) {
    if (param?.name) params[param.name] = param.value;
  }
  return { component: section.component, params };
}

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
 * Derives every piece of data the panel body renders from its raw props.
 *
 * Pure: no React and no hooks, so the component can stay focused on wiring
 * interactions and layout. The derivations themselves are unchanged.
 *
 * @param {*} trace - The raw trace prop.
 * @param {object|null} references - Final chunk reference map.
 * @param {string} [userMessage] - The original user message.
 * @param {number|null} selectedQuery - Active query index, or null for "All".
 * @param {string|null} highlightedRef - The currently highlighted ref.
 * @returns {object} The derived model consumed by the panel.
 */
function buildTraceChunksModel(
  trace,
  references,
  userMessage,
  selectedQuery,
  highlightedRef,
) {
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
  // The Pipeline view shows the selected chunk only when the highlight resolves
  // against a plain-object reference map.
  const selectedChunkInfo =
    isPlainObject(references) && highlightedRef != null
      ? references[highlightedRef]
      : undefined;
  const hasSelectedChunk = isPlainObject(selectedChunkInfo);
  return {
    entries,
    groups,
    hasReferences,
    transformed,
    perQuery,
    discardedRefs,
    provenanceMap,
    kept,
    total,
    effectiveSelectedQuery,
    selectedEntry,
    selectedChunkInfo,
    hasSelectedChunk,
  };
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
 * The muted caption introducing the quoted user message on the Chunks view.
 * @returns {JSX.Element} The caption label.
 */
function YourMessageLabel() {
  const { t } = useTranslation("generative");
  return (
    <Typography
      variant="caption"
      color="text.secondary"
      data-testid="your-message-label"
      sx={{ display: "block", mb: 0.5 }}
    >
      {t("traceChunks.yourMessage")}
    </Typography>
  );
}

/**
 * The user message: an optional muted caption above the quiet quote. The label
 * only exists in the two-view body, so the legacy single column keeps the bare
 * quote exactly as before.
 * @param {object} props
 * @param {string} props.userMessage - The original user message.
 * @param {boolean} props.showLabel - Whether to render the caption.
 * @returns {JSX.Element} The message block.
 */
function UserMessageBlock({ userMessage, showLabel }) {
  if (!showLabel) {
    return <QuestionQuote userMessage={userMessage} />;
  }
  return (
    <Box>
      <YourMessageLabel />
      <QuestionQuote userMessage={userMessage} />
    </Box>
  );
}

UserMessageBlock.propTypes = {
  userMessage: PropTypes.string.isRequired,
  showLabel: PropTypes.bool.isRequired,
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
        // Keeps a card clear of the chat viewport edge.
        scrollMarginTop: "56px",
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
 * The final answer chunks grouped by document, or the empty state when the
 * answer cited none. Shared by the Chunks view and the legacy single column.
 * @param {object} props
 * @param {Array<object>} props.groups - Reference chunks grouped by document.
 * @param {number} props.totalChunks - Total number of reference chunks.
 * @param {string|null} props.highlightedRef - The currently highlighted ref.
 * @param {React.RefObject} props.highlightedCardRef - Ref set when highlighted.
 * @param {Map} props.provenanceMap - Ref → per-query deepest retriever names.
 * @param {Function} props.onSelect - Highlights a chunk ref.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @param {Function} props.onOpenDocument - Opens a document by id.
 * @returns {JSX.Element} The final-chunks panel.
 */
function FinalChunksPanel({
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
  const hasReferences = groups.length > 0;
  return (
    <Box data-testid="final-chunks-panel">
      {hasReferences ? (
        <ChunksSection
          groups={groups}
          totalChunks={totalChunks}
          highlightedRef={highlightedRef}
          highlightedCardRef={highlightedCardRef}
          provenanceMap={provenanceMap}
          onSelect={onSelect}
          onCopy={onCopy}
          onOpenDocument={onOpenDocument}
        />
      ) : (
        <Typography variant="body2" color="text.secondary">
          {t("traceChunks.emptyState")}
        </Typography>
      )}
    </Box>
  );
}

FinalChunksPanel.propTypes = {
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
 * @param {object} props.retrieverComponents - Retriever components by class name.
 * @param {object|null} props.retrieverConfig - Session retriever config tree.
 * @param {Function} props.onChunkClick - Called with a clicked chunk's ref.
 * @returns {JSX.Element} The trace-tree box.
 */
function TraceTrees({
  entries,
  selectedQuery,
  selectedEntry,
  references,
  retrieverComponents,
  retrieverConfig,
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
        retrieverComponents={retrieverComponents}
        configNode={retrieverConfig}
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
  retrieverComponents: PropTypes.object,
  retrieverConfig: PropTypes.object,
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
 * The pipeline view's selected chunk rendered like a highlighted final card.
 *
 * Deliberately not a ChunkCard: that component's `chunk-card-${ref}` testid
 * would collide with the (hidden but mounted) Chunks-view card for the same ref.
 *
 * @param {object} props
 * @param {string} props.chunkRef - The resolved reference key.
 * @param {object} props.info - The resolved reference entry.
 * @param {Map} props.provenanceMap - Ref → per-query deepest retriever names.
 * @param {Function} props.onCopy - Copies the raw chunk text.
 * @param {React.RefObject} props.panelRef - Ref to the panel root (scrolling).
 * @returns {JSX.Element} The selected chunk panel.
 */
function SelectedChunkPanel({
  chunkRef,
  info,
  provenanceMap,
  onCopy,
  panelRef,
}) {
  const { t } = useTranslation("generative");
  const label = resolveChunkLabel(info, t);
  const provenanceText = buildProvenanceText(provenanceMap.get(chunkRef), t);
  return (
    <Paper
      ref={panelRef}
      data-testid="selected-chunk-panel"
      elevation={0}
      sx={{
        p: 2,
        // Keeps the panel clear of the chat viewport edge.
        scrollMarginTop: "56px",
        border: 2,
        borderColor: "primary.main",
        bgcolor: "action.selected",
      }}
    >
      <ChunkCardHeader
        label={label}
        provenanceText={provenanceText}
        chunkText={info.text}
        onCopy={onCopy}
      />
      <ChunkText text={info.text} />
    </Paper>
  );
}

SelectedChunkPanel.propTypes = {
  chunkRef: PropTypes.oneOfType([PropTypes.string, PropTypes.number])
    .isRequired,
  info: PropTypes.object.isRequired,
  provenanceMap: PropTypes.object.isRequired,
  onCopy: PropTypes.func.isRequired,
  panelRef: PropTypes.object.isRequired,
};

/**
 * The pipeline view body, without its former accordion wrapper: the per-query
 * summary, the selector, the selected-query quote, the retriever trees and the
 * discarded candidates, in that order.
 * @param {object} props
 * @param {Array<object>} props.entries - Renderable trace entries.
 * @param {Array<{count: number}>} props.perQuery - Per-query candidate stats.
 * @param {string[]} props.discardedRefs - Refs that never reached the answer.
 * @param {boolean} props.transformed - Whether the query was rewritten.
 * @param {number|null} props.selectedQuery - Active index, or null for "All".
 * @param {object|null} props.selectedEntry - The selected entry, if any.
 * @param {object|null} props.references - Chunk reference map by ref key.
 * @param {object} props.retrieverComponents - Retriever components by class name.
 * @param {object|null} props.retrieverConfig - Session retriever config tree.
 * @param {Function} props.onSelectQuery - Selects a query index (or null).
 * @param {Function} props.onChunkClick - Called with a clicked chunk's ref.
 * @returns {JSX.Element} The pipeline view contents.
 */
function PipelineViewContent({
  entries,
  perQuery,
  discardedRefs,
  transformed,
  selectedQuery,
  selectedEntry,
  references,
  retrieverComponents,
  retrieverConfig,
  onSelectQuery,
  onChunkClick,
}) {
  const showSelectedText =
    transformed &&
    selectedQuery !== null &&
    Boolean(selectedEntry) &&
    typeof selectedEntry.query === "string" &&
    selectedEntry.query.length > 0;
  return (
    <>
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
        retrieverComponents={retrieverComponents}
        retrieverConfig={retrieverConfig}
        onChunkClick={onChunkClick}
      />
      <DiscardedBlock refs={discardedRefs} onDiscardedClick={onChunkClick} />
    </>
  );
}

PipelineViewContent.propTypes = {
  entries: PropTypes.array.isRequired,
  perQuery: PropTypes.array.isRequired,
  discardedRefs: PropTypes.array.isRequired,
  transformed: PropTypes.bool.isRequired,
  selectedQuery: PropTypes.number,
  selectedEntry: PropTypes.object,
  references: PropTypes.object,
  retrieverComponents: PropTypes.object,
  retrieverConfig: PropTypes.object,
  onSelectQuery: PropTypes.func.isRequired,
  onChunkClick: PropTypes.func.isRequired,
};

/**
 * Combined trace + final-chunks inline panel for a RAG response.
 *
 * When a renderable trace is present the body holds two mounted views: a Chunks
 * view (the user message and the final chunks grouped by document) and a
 * Pipeline view (the story strip, the selected chunk or its hint, the per-query
 * selector and retriever trees, and the discarded candidates). Legacy answers
 * with no trace keep a single column of quote plus chunks. Clicking a tree chunk
 * or a chunk card resolves it against the references map: survivors highlight
 * their card and fill the selected-chunk panel, discarded chunks warn.
 *
 * @param {object} props
 * @param {string} props.activeView - The active view (chunks or pipeline).
 * @param {Function} props.onClose - Closes/minimizes the panel.
 * @param {string} [props.id] - Element id targeted by the toggles' aria-controls.
 * @param {string} [props.userMessage] - The original user message.
 * @param {Array|null} [props.trace] - Per-query retriever trace, if any.
 * @param {object|null} [props.references] - Final chunk reference map.
 * @param {number|string} [props.sessionId] - The session that produced the trace.
 * @returns {JSX.Element} The inline panel.
 */
const TraceChunksPanel = ({
  activeView,
  onClose,
  id,
  userMessage,
  trace,
  references,
  sessionId,
}) => {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const navigate = useNavigate();
  const [selectedQuery, setSelectedQuery] = useState(() =>
    filterRenderableEntries(trace).length > 1 ? null : 0,
  );
  const [highlightedRef, setHighlightedRef] = useState(null);
  const [retrieverComponents, setRetrieverComponents] = useState(
    () => retrieverComponentsCache ?? {},
  );
  const [retrieverConfig, setRetrieverConfig] = useState(null);
  const highlightedCardRef = useRef(null);
  const selectedChunkRef = useRef(null);
  const panelRef = useRef(null);
  const bodyRef = useRef(null);
  const previousViewRef = useRef({ view: null, query: null });

  useEffect(() => {
    let cancelled = false;
    loadRetrieverComponents().then((components) => {
      if (!cancelled) setRetrieverComponents(components);
    });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (!sessionId) {
      setRetrieverConfig(null);
      return;
    }
    let cancelled = false;
    getSessionConfiguration(sessionId)
      .then((configuration) => {
        if (!cancelled) {
          setRetrieverConfig(toRetrieverConfig(configuration?.retriever_model));
        }
      })
      .catch(() => {
        if (!cancelled) setRetrieverConfig(null);
      });
    return () => {
      cancelled = true;
    };
  }, [sessionId]);

  useEffect(() => {
    // Bring the sources card into view without yanking the chat away.
    const panel = panelRef.current;
    if (!panel || typeof panel.scrollIntoView !== "function") return;
    const target = panel.parentElement ?? panel;
    const reduceMotion =
      typeof window.matchMedia === "function" &&
      window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    target.scrollIntoView({
      behavior: reduceMotion ? "auto" : "smooth",
      block: "start",
    });
  }, []);

  const {
    entries,
    groups,
    hasReferences,
    transformed,
    perQuery,
    discardedRefs,
    provenanceMap,
    kept,
    total,
    effectiveSelectedQuery,
    selectedEntry,
    selectedChunkInfo,
    hasSelectedChunk,
  } = buildTraceChunksModel(
    trace,
    references,
    userMessage,
    selectedQuery,
    highlightedRef,
  );
  // The Pipeline view is only meaningful when there is a renderable trace.
  const effectiveView =
    activeView === TRACE_VIEW_PIPELINE && entries.length > 0
      ? TRACE_VIEW_PIPELINE
      : TRACE_VIEW_CHUNKS;
  // Legacy answers with no renderable trace keep the single-column body.
  const hasTraceViews = entries.length > 0;
  let panelTitle;
  if (effectiveView === TRACE_VIEW_PIPELINE) {
    panelTitle = t("generative:traceChunks.pipelineTab");
  } else {
    panelTitle = t("generative:traceChunks.chunksTab");
  }

  useEffect(() => {
    const body = bodyRef.current;
    if (!body) return;
    const previous = previousViewRef.current;
    if (
      previous.view === effectiveView &&
      previous.query === effectiveSelectedQuery
    ) {
      return;
    }
    previousViewRef.current = {
      view: effectiveView,
      query: effectiveSelectedQuery,
    };
    body.scrollTop = 0;
  }, [effectiveView, effectiveSelectedQuery]);

  useEffect(() => {
    // Scroll whichever panel currently owns the highlight: the final card in
    // the Chunks view, the selected-chunk panel in the Pipeline view.
    const el =
      effectiveView === TRACE_VIEW_PIPELINE
        ? selectedChunkRef.current
        : highlightedCardRef.current;
    if (el && typeof el.scrollIntoView === "function") {
      const reduceMotion =
        typeof window.matchMedia === "function" &&
        window.matchMedia("(prefers-reduced-motion: reduce)").matches;
      el.scrollIntoView({
        behavior: reduceMotion ? "auto" : "smooth",
        block: "nearest",
      });
    }
  }, [highlightedRef, effectiveView]);

  // The hint invites selecting a tree chunk, so it must only appear when the
  // tree rows are interactive — the very same test RetrieverTraceTree applies.
  const hasUsableReferences =
    isPlainObject(references) && Object.keys(references).length > 0;

  /**
   * Highlights the matching final chunk, or warns when the trace chunk never
   * reached the end of the pipeline.
   * @param {string} chunkRef - The clicked raw reference key.
   */
  const handleChunkClick = useCallback(
    (chunkRef) => {
      if (isPlainObject(references) && isPlainObject(references[chunkRef])) {
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
   * Navigates to a document page and closes the panel.
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
    <Box
      id={id}
      ref={panelRef}
      data-testid="trace-chunks-panel"
      role="group"
      aria-label={t("generative:traceChunks.title")}
      sx={{
        display: "flex",
        flexDirection: "column",
        maxHeight: "60vh",
        minHeight: 0,
        borderTop: 1,
        borderColor: "divider",
        bgcolor: "background.paper",
      }}
    >
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          gap: 1,
          px: 2,
          py: 1,
          flexShrink: 0,
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "action.hover",
        }}
      >
        <Typography
          variant="subtitle1"
          component="div"
          data-testid="trace-panel-title"
          sx={{ fontWeight: 600 }}
        >
          {panelTitle}
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
      </Box>

      <Box
        ref={bodyRef}
        role="group"
        aria-label={panelTitle}
        tabIndex={0}
        sx={{
          p: 2,
          overflowY: "auto",
          overscrollBehavior: "contain",
          minHeight: 0,
          "&:focus-visible": {
            outline: "2px solid",
            outlineColor: "primary.main",
            outlineOffset: -2,
          },
        }}
      >
        {hasTraceViews ? (
          <Stack spacing={2}>
            <Box
              role="group"
              aria-label={t("generative:traceChunks.chunksTab")}
              hidden={effectiveView !== TRACE_VIEW_CHUNKS}
              data-testid="chunks-view"
            >
              <Stack spacing={2}>
                {typeof userMessage === "string" && userMessage.length > 0 && (
                  <UserMessageBlock userMessage={userMessage} showLabel />
                )}

                <FinalChunksPanel
                  groups={groups}
                  totalChunks={kept}
                  highlightedRef={highlightedRef}
                  highlightedCardRef={highlightedCardRef}
                  provenanceMap={provenanceMap}
                  onSelect={setHighlightedRef}
                  onCopy={handleCopyChunk}
                  onOpenDocument={handleOpenDocument}
                />
              </Stack>
            </Box>

            <Box
              role="group"
              aria-label={t("generative:traceChunks.pipelineTab")}
              hidden={effectiveView !== TRACE_VIEW_PIPELINE}
              data-testid="pipeline-view"
            >
              <Stack spacing={2}>
                {hasSelectedChunk ? (
                  <SelectedChunkPanel
                    chunkRef={highlightedRef}
                    info={selectedChunkInfo}
                    provenanceMap={provenanceMap}
                    onCopy={handleCopyChunk}
                    panelRef={selectedChunkRef}
                  />
                ) : hasUsableReferences ? (
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    data-testid="selected-chunk-hint"
                  >
                    {t("generative:traceChunks.selectedChunkHint")}
                  </Typography>
                ) : null}

                {hasReferences && (
                  <StoryStrip
                    transformed={transformed}
                    queryCount={entries.length}
                    kept={kept}
                    total={total}
                  />
                )}

                <PipelineViewContent
                  entries={entries}
                  perQuery={perQuery}
                  discardedRefs={discardedRefs}
                  transformed={transformed}
                  selectedQuery={effectiveSelectedQuery}
                  selectedEntry={selectedEntry}
                  references={references}
                  retrieverComponents={retrieverComponents}
                  retrieverConfig={retrieverConfig}
                  onSelectQuery={setSelectedQuery}
                  onChunkClick={handleChunkClick}
                />
              </Stack>
            </Box>
          </Stack>
        ) : (
          <Stack spacing={2}>
            {typeof userMessage === "string" && userMessage.length > 0 && (
              <UserMessageBlock userMessage={userMessage} showLabel={false} />
            )}

            <FinalChunksPanel
              groups={groups}
              totalChunks={kept}
              highlightedRef={highlightedRef}
              highlightedCardRef={highlightedCardRef}
              provenanceMap={provenanceMap}
              onSelect={setHighlightedRef}
              onCopy={handleCopyChunk}
              onOpenDocument={handleOpenDocument}
            />
          </Stack>
        )}
      </Box>
    </Box>
  );
};

TraceChunksPanel.propTypes = {
  activeView: PropTypes.oneOf([TRACE_VIEW_CHUNKS, TRACE_VIEW_PIPELINE])
    .isRequired,
  onClose: PropTypes.func.isRequired,
  id: PropTypes.string,
  userMessage: PropTypes.string,
  trace: PropTypes.array,
  references: PropTypes.object,
  sessionId: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
};

export default TraceChunksPanel;
