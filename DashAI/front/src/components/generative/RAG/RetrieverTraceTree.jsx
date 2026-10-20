import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import SchemaIcon from "@mui/icons-material/Schema";
import AccountTreeIcon from "@mui/icons-material/AccountTree";
import { resolveLocalizedText } from "../../../utils/localize";
import { resolveRetrieverRepresentation } from "./retrieverRepresentation";
import { asArray, isPlainObject, resolveChunkLabel } from "./traceUtils";

// Base horizontal unit (px) for the tree indentation, mirroring the geometry
// used by CompositeRetrieverBuilder: a card at depth d is indented d*INDENT px
// and the vertical spine connecting a level sits INDENT/2 px to the left of the
// card, so consecutive spine columns are exactly INDENT px apart.
const INDENT = 40;

// Extra offset that pushes a node's own chunk rows under its card.
const CHUNK_INDENT = 28;

const missingChipSx = {
  display: "inline-block",
  border: 1,
  borderColor: "divider",
  borderRadius: "4px",
  px: 0.5,
  color: "text.secondary",
  fontFamily: "monospace",
  fontSize: "0.75rem",
  lineHeight: 1.4,
};

/**
 * Checks whether a reference map carries at least one entry.
 * @param {object|null|undefined} references - The chunk reference map.
 * @returns {boolean} True when the map is a non-empty object.
 */
function hasEntries(references) {
  return isPlainObject(references) && Object.keys(references).length > 0;
}

/**
 * Looks up a chunk's resolved info in the reference map.
 * @param {object|null} references - The chunk reference map.
 * @param {string} chunkRef - The raw "<doc>_<pos>" reference key.
 * @returns {object|undefined} The matching reference entry, if any.
 */
function resolveChunkInfo(references, chunkRef) {
  if (!isPlainObject(references)) return undefined;
  return references[chunkRef];
}

/**
 * Pick the configured child that corresponds to a trace child node.
 *
 * Trace children may repeat a retriever (LLM-evaluated rounds) or contain
 * siblings of the same class (parallel retrievers). Match by class name and
 * occurrence order, reusing the last configured entry when the trace repeats a
 * child more often than the configuration declares it.
 *
 * @param {*} configuredChildren - The configured child refs of the parent.
 * @param {Array<object>} traceChildren - The rendered trace children.
 * @param {object} child - The trace child being rendered.
 * @returns {object|null} The matching `{component, params}` ref, or null.
 */
function resolveChildConfig(configuredChildren, traceChildren, child) {
  if (!Array.isArray(configuredChildren)) return null;

  const sameName = configuredChildren.filter(
    (entry) => entry?.component === child?.name,
  );
  if (sameName.length === 0) return null;

  const occurrence = traceChildren
    .filter((entry) => entry?.name === child?.name)
    .indexOf(child);
  const index = occurrence < 0 ? 0 : Math.min(occurrence, sameName.length - 1);
  return sameName[index] || null;
}

/**
 * A single clickable chunk row under a retriever node, optionally carrying the
 * cross-encoder score inline at the right edge.
 *
 * Resolved refs show "document · chunk" and unresolved refs fall back to a raw
 * chip. Rows are muted but still clickable when the ref is missing from a
 * non-empty reference map, and become fully inert when the map itself is empty.
 *
 * @param {object} props
 * @param {string} props.chunkRef - The raw "<doc>_<pos>" reference key.
 * @param {object} [props.info] - The resolved reference entry, if any.
 * @param {number} [props.score] - The candidate's score for this node, if any.
 * @param {boolean} props.interactive - Whether the row responds to clicks.
 * @param {Function} props.onClick - Called with the raw ref and info when clicked.
 * @returns {JSX.Element} The chunk row.
 */
function TreeChunkRow({ chunkRef, info, score, interactive, onClick }) {
  const { t } = useTranslation("generative");
  const handleClick = interactive ? () => onClick(chunkRef, info) : undefined;
  let scoreLabel = null;
  if (typeof score === "number" && Number.isFinite(score)) {
    scoreLabel = score.toFixed(3);
  }

  /**
   * Activates the row with Enter/Space when it is interactive.
   * @param {React.KeyboardEvent} event - The keydown event.
   */
  const handleKeyDown = (event) => {
    if (!interactive) return;
    if (event.key !== "Enter" && event.key !== " ") return;
    event.preventDefault();
    onClick(chunkRef, info);
  };

  return (
    <Box
      data-testid={`tree-chunk-${chunkRef}`}
      role={interactive ? "button" : undefined}
      tabIndex={interactive ? 0 : undefined}
      onClick={handleClick}
      onKeyDown={handleKeyDown}
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "space-between",
        gap: 2,
        width: "fit-content",
        minWidth: 220,
        cursor: interactive ? "pointer" : "default",
        "&:focus-visible": {
          outline: "2px solid",
          outlineColor: "primary.main",
          outlineOffset: 2,
        },
      }}
    >
      {info ? (
        <Typography component="span" variant="caption">
          <Box
            component="span"
            sx={{ fontWeight: "bold", color: "text.primary" }}
          >
            {info.document_name ?? chunkRef}
          </Box>
          {" · "}
          <Box component="span" sx={{ color: "text.secondary" }}>
            {resolveChunkLabel(info, t)}
          </Box>
        </Typography>
      ) : (
        <Box component="span" sx={missingChipSx}>
          {chunkRef}
        </Box>
      )}
      {scoreLabel != null && (
        <Box
          component="span"
          sx={(theme) => ({
            ...theme.typography.code,
            color: "text.secondary",
            flexShrink: 0,
          })}
        >
          {scoreLabel}
        </Box>
      )}
    </Box>
  );
}

/**
 * Read-only renderer for one retriever node of a RAG trace.
 *
 * Draws a left-to-right tree that mirrors CompositeRetrieverBuilder's geometry:
 * a card (purple for composites, amber for leaves) followed by its own chunk
 * rows with their cross-encoder scores inline, and its children recursively.
 *
 * @param {object} props
 * @param {object} props.node - The trace retriever node to render.
 * @param {object|null} [props.references] - Chunk reference map by ref key.
 * @param {object} [props.retrieverComponents] - Retriever components by class name.
 * @param {object|null} [props.configNode] - Matching session retriever config.
 * @param {Function} [props.onChunkClick] - Called with (chunkRef, info|undefined).
 * @param {number} [props.depth=0] - Current indentation depth.
 * @param {boolean} [props.isRoot=true] - Whether this is the root node.
 * @returns {JSX.Element|null} The node UI, or null for non-object nodes.
 */
function RetrieverTraceTree({
  node,
  references,
  retrieverComponents = {},
  configNode = null,
  onChunkClick,
  depth = 0,
  isRoot = true,
}) {
  const { t, i18n } = useTranslation("generative");

  if (!isPlainObject(node)) return null;

  const chunks = asArray(node.chunks);
  const children = asArray(node.children).filter(isPlainObject);
  const scoreByRef = new Map(
    asArray(node.scores)
      .filter((entry) => isPlainObject(entry) && typeof entry.ref === "string")
      .map((entry) => [entry.ref, entry.score]),
  );
  const isComposite = children.length > 0;
  const cardX = depth * INDENT;
  const interactive =
    hasEntries(references) && typeof onChunkClick === "function";
  const component = retrieverComponents?.[node.name];
  const effectiveConfig =
    configNode?.component === node.name ? configNode : null;
  const traceRepresentation = resolveLocalizedText(node.representation, i18n);
  const configRepresentation = resolveRetrieverRepresentation(
    component,
    effectiveConfig?.params,
    i18n,
  );
  const representation = traceRepresentation || configRepresentation;
  const description =
    resolveLocalizedText(node.description, i18n) ||
    resolveLocalizedText(component?.description, i18n);
  const caption = representation || description || null;

  return (
    <Box>
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          gap: 1,
          ml: `${cardX}px`,
          position: "relative",
        }}
      >
        {!isRoot && (
          <Box
            data-conn
            sx={{
              position: "absolute",
              left: `${-INDENT / 2}px`,
              top: "50%",
              width: `${INDENT / 2}px`,
              borderTop: "1px solid",
              borderColor: "divider",
            }}
          />
        )}
        <Box
          data-card
          sx={{
            display: "flex",
            alignItems: "center",
            gap: 1,
            px: 1.5,
            py: 1,
            border: "1px solid",
            borderColor: isComposite
              ? "accent.purpleBorder"
              : "accent.amberBorder",
            borderRadius: 1,
            backgroundColor: "background.paper",
          }}
        >
          {isComposite ? (
            <AccountTreeIcon sx={{ fontSize: 18, color: "accent.purple" }} />
          ) : (
            <SchemaIcon sx={{ fontSize: 18, color: "accent.amber" }} />
          )}
          <Box
            sx={{
              display: "flex",
              flexDirection: "column",
              minWidth: "fit-content",
              maxWidth: 480,
            }}
          >
            <Typography variant="body2">{node.name}</Typography>
            {caption && (
              <Typography
                variant="caption"
                color="text.secondary"
                sx={{
                  maxWidth: 420,
                  overflowWrap: "anywhere",
                }}
              >
                {caption}
              </Typography>
            )}
          </Box>
          <Typography variant="caption" color="text.secondary">
            {t("traceChunks.chunksLabel", { count: chunks.length })}
          </Typography>
        </Box>
      </Box>

      {chunks.length > 0 && (
        <Box
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: 0.25,
            mt: 0.5,
            ml: `${cardX + CHUNK_INDENT}px`,
          }}
        >
          {chunks.map((chunkRef, index) => (
            <TreeChunkRow
              key={`${chunkRef}-${index}`}
              chunkRef={chunkRef}
              info={resolveChunkInfo(references, chunkRef)}
              score={scoreByRef.get(chunkRef)}
              interactive={interactive}
              onClick={onChunkClick}
            />
          ))}
        </Box>
      )}

      {children.length > 0 && (
        <Box sx={{ position: "relative" }}>
          {children.map((child, index) => (
            <Box
              key={`${child?.name ?? "node"}-${index}`}
              sx={{ position: "relative" }}
            >
              <Box
                data-spine
                sx={{
                  position: "absolute",
                  left: `${cardX + INDENT / 2}px`,
                  top: 0,
                  bottom: 0,
                  width: "1px",
                  borderLeft: "1px solid",
                  borderColor: "divider",
                }}
              />
              <RetrieverTraceTree
                node={child}
                references={references}
                retrieverComponents={retrieverComponents}
                configNode={resolveChildConfig(
                  effectiveConfig?.params?.children,
                  children,
                  child,
                )}
                onChunkClick={onChunkClick}
                depth={depth + 1}
                isRoot={false}
              />
            </Box>
          ))}
        </Box>
      )}
    </Box>
  );
}

RetrieverTraceTree.propTypes = {
  node: PropTypes.object,
  references: PropTypes.object,
  retrieverComponents: PropTypes.object,
  configNode: PropTypes.object,
  onChunkClick: PropTypes.func,
  depth: PropTypes.number,
  isRoot: PropTypes.bool,
};

export default RetrieverTraceTree;
