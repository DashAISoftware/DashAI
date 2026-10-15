import { useState, useEffect, useRef, useCallback } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import {
  Box,
  Typography,
  Stack,
  Tooltip,
  Chip,
  Paper,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
} from "@mui/material";
import {
  Article as ArticleIcon,
  ContentCopy as CopyIcon,
  OpenInNew as OpenInNewIcon,
} from "@mui/icons-material";
import RetrieverTraceTree from "./RetrieverTraceTree";

/**
 * Checks whether a value is a non-null, non-array object.
 * @param {*} value - The value to inspect.
 * @returns {boolean} True for plain objects only.
 */
function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/**
 * Checks whether a trace entry carries a retriever object.
 * @param {object} entry - A trace entry.
 * @returns {boolean} True when `entry.retriever` is a plain object.
 */
function hasObjectRetriever(entry) {
  return isPlainObject(entry?.retriever);
}

/**
 * A trace is query-transformed when more than one query was used, or when the
 * single transformed query differs from the original user message. When the
 * transformation ran but echoed the message back, it is indistinguishable and
 * treated as untransformed.
 * @param {Array<object>} entries - Renderable trace entries.
 * @param {string} [userMessage] - The original user message.
 * @returns {boolean} True when the trace reflects a query transformation.
 */
function isQueryTransformed(entries, userMessage) {
  if (entries.length <= 1) {
    const only = entries[0];
    return typeof only?.query === "string" && only.query !== userMessage;
  }
  return true;
}

/**
 * Resolves a document title from a reference entry using the shared fallback
 * chain (title, name, then the localised "Document {{id}}" fallback).
 * @param {object} [info] - The reference entry for the document.
 * @param {number|string} docId - The document identifier.
 * @param {Function} t - i18n translate function.
 * @returns {string} The display title.
 */
function getDocumentTitle(info, docId, t) {
  if (info?.document_title) return info.document_title;
  if (info?.document_name) return info.document_name;
  if (info?.title) return info.title;
  if (info?.name) return info.name;
  return t("generative:traceChunks.fallbackTitle", { id: docId });
}

/**
 * Filters a trace list down to the entries that render (object retrievers).
 * @param {*} trace - The raw trace prop.
 * @returns {Array<object>} The renderable trace entries.
 */
function filterRenderableEntries(trace) {
  return Array.isArray(trace) ? trace.filter(hasObjectRetriever) : [];
}

/**
 * Groups the final reference chunks by document, preserving first-appearance
 * order, and keeps each chunk's raw ref alongside its payload. Entries whose
 * value is not a plain object are dropped so a corrupt map can never reach the
 * rendering path.
 * @param {object|null} references - Chunk reference map by ref key.
 * @returns {Array<{docId: *, chunks: Array<object>}>} The ordered groups.
 */
function groupReferencesByDocument(references) {
  if (!isPlainObject(references)) return [];
  const order = [];
  const byDocument = new Map();
  Object.entries(references).forEach(([ref, info]) => {
    if (!isPlainObject(info)) return;
    const docId = info?.document_id;
    if (!byDocument.has(docId)) {
      byDocument.set(docId, []);
      order.push(docId);
    }
    byDocument.get(docId).push({ ref, ...info });
  });
  return order.map((docId) => ({ docId, chunks: byDocument.get(docId) }));
}

/**
 * Combined trace + final-chunks modal for a RAG response.
 *
 * The title is a static localised heading. The two-panel body's left column
 * stacks the header (the original user message in a bubble, the
 * transformed-sources label, the query-selector chips, and the raw text of the
 * selected query whenever a specific query is active) above the retriever trace
 * for the selected query (every query stacked, each under a "Query N" heading,
 * when "All" is active); the right column renders every chunk that reached the
 * end of the pipeline, grouped by document. Clicking a trace chunk or a
 * right-panel chunk card resolves it against the references map: surviving
 * chunks highlight their card, discarded chunks raise a snackbar instead.
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
      el.scrollIntoView({ behavior: "smooth", block: "nearest" });
    }
  }, [highlightedRef]);

  const renderableEntries = filterRenderableEntries(trace);
  const groups = groupReferencesByDocument(references);
  const hasReferences = groups.length > 0;

  const showSelector = isQueryTransformed(renderableEntries, userMessage);

  const selectedEntry =
    selectedQuery === null ? null : renderableEntries[selectedQuery];
  const showTree =
    renderableEntries.length > 0 &&
    (selectedQuery === null || Boolean(selectedEntry));

  const highlightedInfo =
    highlightedRef && isPlainObject(references)
      ? references[highlightedRef]
      : null;

  const selectedDocId = highlightedInfo?.document_id ?? groups[0]?.docId;

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
   * Copies a chunk's text to the clipboard with escaped newlines restored.
   * @param {string} chunkText - The raw chunk text.
   */
  const handleCopyChunk = useCallback(async (chunkText) => {
    if (typeof chunkText !== "string") return;
    try {
      await navigator.clipboard.writeText(chunkText.replace(/\\n/g, "\n"));
    } catch {
      // Clipboard access can be unavailable; copying is best effort.
    }
  }, []);

  /**
   * Navigates to the selected chunk's document before closing the dialog.
   */
  const handleOpenDocument = () => {
    if (selectedDocId == null) return;
    navigate(`/app/data/documents/${selectedDocId}`);
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      // MUI v7: PaperProps is deprecated in favour of slotProps.paper.
      slotProps={{ paper: { sx: { maxHeight: "85vh" } } }}
    >
      <DialogTitle
        sx={{
          bgcolor: "background.paper",
          display: "flex",
          justifyContent: "center",
          alignItems: "center",
          gap: 1,
        }}
      >
        <ArticleIcon color="primary" sx={{ flexShrink: 0 }} />
        <Typography
          variant="h6"
          component="div"
          noWrap
          data-testid="trace-chunks-title"
          sx={{ textAlign: "center" }}
        >
          {t("generative:traceChunks.title")}
        </Typography>
      </DialogTitle>

      <DialogContent
        dividers
        sx={{
          bgcolor: "background.paper",
          maxHeight: "70vh",
          // On sm+ the two columns scroll independently, so the outer panel
          // must never scroll itself. On xs the columns stack and exceed the
          // box, so the outer panel becomes the recovery scroll container.
          overflow: { xs: "auto", sm: "hidden" },
        }}
      >
        <Stack
          direction={{ xs: "column", sm: "row" }}
          spacing={2}
          sx={{ alignItems: "stretch" }}
        >
          <Box
            sx={{
              flex: 1,
              minWidth: 0,
              display: "flex",
              flexDirection: "column",
              // sm+: this column is its own scroll container. xs: the stacked
              // columns paint fully and the outer DialogContent handles scroll.
              overflowY: { xs: "visible", sm: "auto" },
              maxHeight: { xs: "none", sm: "58vh" },
              pr: 1,
            }}
          >
            {typeof userMessage === "string" && userMessage.length > 0 && (
              <Box sx={{ mb: 2 }}>
                <Typography variant="body2" data-testid="your-message-label">
                  {t("generative:traceChunks.yourMessageLabel")}
                </Typography>
                <Paper
                  data-testid="user-message-box"
                  elevation={0}
                  sx={{
                    backgroundColor: "ui.box",
                    py: 1.5,
                    px: 4,
                    borderRadius: 2,
                    width: "fit-content",
                    maxWidth: "100%",
                  }}
                >
                  <Typography
                    variant="body1"
                    data-testid="your-message-text"
                    sx={{ whiteSpace: "pre-wrap", wordBreak: "break-word" }}
                  >
                    {userMessage}
                  </Typography>
                </Paper>
              </Box>
            )}

            {showSelector && (
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {t("generative:traceChunks.transformedLabel")}
              </Typography>
            )}

            {showSelector && (
              <Box
                data-testid="query-selector"
                sx={{ display: "flex", flexWrap: "wrap", gap: 1, mb: 2 }}
              >
                {renderableEntries.length > 1 && (
                  <Chip
                    data-testid="query-chip"
                    size="small"
                    label={t("generative:traceChunks.allQueriesChip")}
                    color={selectedQuery === null ? "primary" : "default"}
                    variant={selectedQuery === null ? "filled" : "outlined"}
                    onClick={() => setSelectedQuery(null)}
                  />
                )}
                {renderableEntries.map((entry, index) => (
                  <Tooltip
                    key={index}
                    title={typeof entry?.query === "string" ? entry.query : ""}
                  >
                    <Chip
                      data-testid="query-chip"
                      size="small"
                      label={t("generative:traceChunks.queryTooltip", {
                        index: index + 1,
                      })}
                      color={selectedQuery === index ? "primary" : "default"}
                      variant={selectedQuery === index ? "filled" : "outlined"}
                      onClick={() => setSelectedQuery(index)}
                    />
                  </Tooltip>
                ))}
              </Box>
            )}

            {showSelector &&
              selectedQuery !== null &&
              selectedEntry &&
              typeof selectedEntry.query === "string" &&
              selectedEntry.query && (
                <Typography
                  variant="body2"
                  color="text.secondary"
                  data-testid="selected-query-text"
                  sx={{ mt: 0.5, mb: 2, wordBreak: "break-word" }}
                >
                  {selectedEntry.query}
                </Typography>
              )}

            {showTree && (
              <Box
                data-testid="trace-tree"
                sx={{
                  flex: 1,
                  minWidth: 0,
                  border: 1,
                  borderColor: "divider",
                  borderRadius: 1,
                  p: 2,
                  backgroundColor: "background.box",
                }}
              >
                {selectedQuery === null
                  ? renderableEntries.map((entry, index) => (
                      <Box
                        key={index}
                        sx={{
                          mb: index < renderableEntries.length - 1 ? 2 : 0,
                        }}
                      >
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: "bold", mb: 0.5 }}
                        >
                          {t("generative:traceChunks.queryTooltip", {
                            index: index + 1,
                          })}
                        </Typography>
                        <RetrieverTraceTree
                          node={entry.retriever}
                          references={references}
                          onChunkClick={handleChunkClick}
                        />
                      </Box>
                    ))
                  : selectedEntry && (
                      <Box>
                        <Typography
                          variant="body2"
                          sx={{ fontWeight: "bold", mb: 0.5 }}
                        >
                          {t("generative:traceChunks.queryTooltip", {
                            index: selectedQuery + 1,
                          })}
                        </Typography>
                        <RetrieverTraceTree
                          node={selectedEntry.retriever}
                          references={references}
                          onChunkClick={handleChunkClick}
                        />
                      </Box>
                    )}
              </Box>
            )}
          </Box>

          <Box
            data-testid="final-chunks-panel"
            sx={{
              flex: 1,
              minWidth: 0,
              overflow: { xs: "visible", sm: "auto" },
              maxHeight: { xs: "none", sm: "58vh" },
            }}
          >
            {hasReferences ? (
              groups.map((group) => (
                <Box
                  key={group.docId}
                  data-testid={`doc-group-${group.docId}`}
                  sx={{ mb: 2 }}
                >
                  <Box
                    sx={{
                      display: "flex",
                      alignItems: "center",
                      justifyContent: "center",
                      gap: 1,
                    }}
                  >
                    <ArticleIcon color="primary" sx={{ fontSize: 18 }} />
                    <Typography variant="subtitle1">
                      {getDocumentTitle(group.chunks[0], group.docId, t)}
                    </Typography>
                  </Box>
                  <Typography
                    variant="body2"
                    color="text.secondary"
                    align="center"
                    sx={{ mb: 1 }}
                  >
                    {t("generative:traceChunks.groupChunksCount", {
                      count: group.chunks.length,
                    })}
                  </Typography>

                  <Stack spacing={1}>
                    {group.chunks.map((chunk) => {
                      const isHighlighted = chunk.ref === highlightedRef;
                      return (
                        <Paper
                          key={chunk.ref}
                          ref={isHighlighted ? highlightedCardRef : null}
                          data-testid={
                            isHighlighted
                              ? "highlighted-chunk-card"
                              : `chunk-card-${chunk.ref}`
                          }
                          elevation={0}
                          onClick={() => setHighlightedRef(chunk.ref)}
                          role="button"
                          tabIndex={0}
                          onKeyDown={(event) => {
                            if (event.key !== "Enter" && event.key !== " ")
                              return;
                            event.preventDefault();
                            setHighlightedRef(chunk.ref);
                          }}
                          sx={{
                            p: 2,
                            cursor: "pointer",
                            border: isHighlighted ? 2 : 1,
                            borderColor: isHighlighted
                              ? "primary.main"
                              : "divider",
                            bgcolor: isHighlighted
                              ? "action.selected"
                              : "background.paper",
                            ...(isHighlighted
                              ? {}
                              : {
                                  "&:hover": {
                                    backgroundColor: "action.hover",
                                  },
                                }),
                          }}
                        >
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
                            >
                              <Box
                                sx={{
                                  width: 6,
                                  height: 6,
                                  borderRadius: "50%",
                                  backgroundColor: "primary.main",
                                  flexShrink: 0,
                                }}
                              />
                              <Typography variant="subtitle2">
                                {chunk.page != null
                                  ? t(
                                      "generative:traceChunks.chunkLabelWithPage",
                                      {
                                        position: chunk.document_position,
                                        page: chunk.page,
                                      },
                                    )
                                  : t("generative:traceChunks.chunkLabel", {
                                      position: chunk.document_position,
                                    })}
                              </Typography>
                            </Stack>

                            <Tooltip title={t("common:copy", "Copy")}>
                              <IconButton
                                size="small"
                                onClick={(event) => {
                                  event.stopPropagation();
                                  handleCopyChunk(chunk.text);
                                }}
                                aria-label={t("common:copy", "Copy")}
                                sx={{
                                  color: "text.secondary",
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

                          <Typography
                            variant="body2"
                            sx={{ lineHeight: 1.6, whiteSpace: "pre-wrap" }}
                          >
                            {typeof chunk.text === "string"
                              ? chunk.text.replace(/\\n/g, "\n")
                              : ""}
                          </Typography>
                        </Paper>
                      );
                    })}
                  </Stack>
                </Box>
              ))
            ) : (
              <Typography variant="body2" color="text.secondary">
                {t("generative:traceChunks.emptyState")}
              </Typography>
            )}
          </Box>
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button
          startIcon={<OpenInNewIcon />}
          disabled={selectedDocId == null}
          onClick={handleOpenDocument}
        >
          {t("generative:traceChunks.openDocument")}
        </Button>
        <Button onClick={onClose} variant="outlined">
          {t("common:close")}
        </Button>
      </DialogActions>
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
