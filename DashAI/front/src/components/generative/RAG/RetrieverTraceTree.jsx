import React from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import SchemaIcon from "@mui/icons-material/Schema";
import AccountTreeIcon from "@mui/icons-material/AccountTree";

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
  color: "text.disabled",
  fontFamily: "monospace",
  fontSize: "0.75rem",
  lineHeight: 1.4,
};

/**
 * Checks whether a value is a non-null, non-array object.
 * @param {*} value - The value to inspect.
 * @returns {boolean} True for plain objects only.
 */
function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/**
 * Coerces a possibly-missing list into an array.
 * @param {*} value - The value to coerce.
 * @returns {Array} The value itself when it is an array, otherwise an empty one.
 */
function asArray(value) {
  return Array.isArray(value) ? value : [];
}

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
 * Builds the human label for a resolved chunk ("Chunk N" or "Chunk N, page P").
 * @param {object} info - The resolved reference entry.
 * @param {Function} t - i18n translate function.
 * @returns {string} The translated chunk label.
 */
function resolveChunkLabel(info, t) {
  return info.page != null
    ? t("traceChunks.chunkLabelWithPage", {
        position: info.document_position,
        page: info.page,
      })
    : t("traceChunks.chunkLabel", { position: info.document_position });
}

/**
 * A single clickable chunk row under a retriever node.
 *
 * Resolved refs show "document · chunk" and unresolved refs fall back to a raw
 * chip. Rows are muted but still clickable when the ref is missing from a
 * non-empty reference map, and become fully inert when the map itself is empty.
 *
 * @param {object} props
 * @param {string} props.chunkRef - The raw "<doc>_<pos>" reference key.
 * @param {object} [props.info] - The resolved reference entry, if any.
 * @param {boolean} props.interactive - Whether the row responds to clicks.
 * @param {Function} props.onClick - Called with the raw ref and info when clicked.
 * @returns {JSX.Element} The chunk row.
 */
function TreeChunkRow({ chunkRef, info, interactive, onClick }) {
  const { t } = useTranslation("generative");
  const handleClick = interactive ? () => onClick(chunkRef, info) : undefined;

  if (!info) {
    return (
      <Box
        data-testid={`tree-chunk-${chunkRef}`}
        role={interactive ? "button" : undefined}
        onClick={handleClick}
        sx={{ ...missingChipSx, cursor: interactive ? "pointer" : "default" }}
      >
        {chunkRef}
      </Box>
    );
  }

  return (
    <Typography
      data-testid={`tree-chunk-${chunkRef}`}
      component="span"
      variant="caption"
      role={interactive ? "button" : undefined}
      onClick={handleClick}
      sx={{ cursor: interactive ? "pointer" : "default", width: "fit-content" }}
    >
      <Box component="span" sx={{ fontWeight: "bold", color: "text.primary" }}>
        {info.document_name ?? chunkRef}
      </Box>
      {" · "}
      <Box component="span" sx={{ color: "text.secondary" }}>
        {resolveChunkLabel(info, t)}
      </Box>
    </Typography>
  );
}

/**
 * Read-only renderer for one retriever node of a RAG trace.
 *
 * Draws a left-to-right tree that mirrors CompositeRetrieverBuilder's geometry:
 * a card (purple for composites, amber for leaves) followed by its own chunk
 * rows, optional cross-encoder score rows, and its children recursively.
 *
 * @param {object} props
 * @param {object} props.node - The trace retriever node to render.
 * @param {object|null} [props.references] - Chunk reference map by ref key.
 * @param {Function} [props.onChunkClick] - Called with (chunkRef, info|undefined).
 * @param {number} [props.depth=0] - Current indentation depth.
 * @param {boolean} [props.isRoot=true] - Whether this is the root node.
 * @returns {JSX.Element|null} The node UI, or null for non-object nodes.
 */
function RetrieverTraceTree({
  node,
  references,
  onChunkClick,
  depth = 0,
  isRoot = true,
}) {
  const { t } = useTranslation("generative");

  if (!isPlainObject(node)) return null;

  const chunks = asArray(node.chunks);
  const children = asArray(node.children).filter(isPlainObject);
  const scores = asArray(node.scores);
  const isComposite = children.length > 0;
  const cardX = depth * INDENT;
  const interactive =
    hasEntries(references) && typeof onChunkClick === "function";

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
          <Typography variant="body2">{node.name}</Typography>
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
              interactive={interactive}
              onClick={onChunkClick}
            />
          ))}
        </Box>
      )}

      {scores.length > 0 && (
        <Box sx={{ mt: 0.5, ml: `${cardX + CHUNK_INDENT}px` }}>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ fontWeight: "medium" }}
          >
            {t("traceChunks.scoresLabel")}
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
  onChunkClick: PropTypes.func,
  depth: PropTypes.number,
  isRoot: PropTypes.bool,
};

export default RetrieverTraceTree;
