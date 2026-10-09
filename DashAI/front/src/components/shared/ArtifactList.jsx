import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";

import ArtifactViewer from "./ArtifactViewer";
import ArtifactGroupSelector from "./ArtifactGroupSelector";

/**
 * Build the edit props shared by every leaf.
 *
 * Whether a leaf can be reset is read off the artifact itself: the backend
 * stamps `overridden` on any leaf whose stored edit it just applied, so the
 * undo button appears exactly on the plots that have something to undo,
 * without the caller tracking indexes of its own.
 */
function leafProps(artifact, { onSaveOverride, onResetOverride } = {}) {
  return {
    canReset: Boolean(artifact.overridden),
    onSaveEdit: onSaveOverride
      ? (figure) => onSaveOverride(artifact.index, figure)
      : null,
    onResetEdit: onResetOverride ? () => onResetOverride(artifact.index) : null,
  };
}

/**
 * Lay out a batch of leaf artifacts: the first artifact fills the row beside
 * whatever `leading` element is passed (a selector, or nothing); any further
 * artifacts stack below at full width, most recent first. `siblings` is the
 * full artifact list of the batch so the fullscreen viewer can navigate
 * between them.
 */
function ArtifactBatch({
  artifacts,
  siblings,
  ctx,
  leading = null,
  leadingFlex,
  leadingMinWidth = 0,
  siblingOffset = 0,
}) {
  const renderLeaf = (artifact, i) => (
    <ArtifactViewer
      key={i}
      artifact={artifact}
      siblingArtifacts={siblings}
      siblingIndex={siblingOffset + i}
      {...leafProps(artifact, ctx)}
    />
  );

  const [firstArtifact, ...rest] = artifacts;
  const stacked = rest.map((artifact, i) => ({ artifact, i: i + 1 })).reverse();

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 3, width: "100%" }}
    >
      <Box sx={{ display: "flex", gap: 3, alignItems: "stretch" }}>
        {leading && (
          <Box
            sx={{
              flex: leadingFlex,
              minWidth: leadingMinWidth,
              // Flex + stretch so the leading element (a table whose root is
              // height:100%) fills this cell and matches the first artifact's
              // height instead of collapsing to its own content.
              display: "flex",
              minHeight: 0,
            }}
          >
            {leading}
          </Box>
        )}
        <Box sx={{ flex: 1, minWidth: 0 }}>{renderLeaf(firstArtifact, 0)}</Box>
      </Box>
      {stacked.map(({ artifact, i }) => renderLeaf(artifact, i))}
    </Box>
  );
}

ArtifactBatch.propTypes = {
  artifacts: PropTypes.array.isRequired,
  siblings: PropTypes.array.isRequired,
  ctx: PropTypes.object.isRequired,
  leading: PropTypes.node,
  leadingFlex: PropTypes.string,
  leadingMinWidth: PropTypes.number,
  siblingOffset: PropTypes.number,
};

/**
 * Render a GroupedArtifacts item: a selector listing every group, beside the
 * selected group's first artifact (with the rest stacked below). Holds its own
 * selection state, so multiple selectors on one card are independent.
 *
 * The selector defaults to a plain title list. A caller with something richer
 * to show (a local explainer listing each explained instance's feature values)
 * passes `renderGroupSelector` and, when that widget needs the extra room,
 * `wideSelector`. `renderStory` appends a caller supplied element below the
 * selected group's artifacts, given the group itself.
 */
function GroupedArtifactsView({
  grouped,
  ctx,
  renderGroupSelector = null,
  wideSelector = false,
  fallbackGroupTitle = null,
  renderStory = null,
  selected: selectedProp = null,
  onSelect = null,
}) {
  const [localSelected, setLocalSelected] = useState(0);
  const selected = selectedProp ?? localSelected;
  const setSelected = onSelect ?? setLocalSelected;
  const groups = grouped.groups ?? [];
  if (groups.length === 0) return null;

  const group = groups[selected] ?? groups[0];
  const titles = groups.map(
    (g, i) =>
      g.title ??
      (fallbackGroupTitle ? fallbackGroupTitle(i) : `Group ${i + 1}`),
  );

  // Fullscreen navigation spans every group's artifacts (flattened), so the
  // viewer can page across groups even when each group has a single artifact.
  // The selected group's artifacts occupy the slice starting at `offset`.
  const allArtifacts = groups.flatMap((g) => g.artifacts);
  const offset = groups
    .slice(0, selected)
    .reduce((n, g) => n + g.artifacts.length, 0);

  // Rendered directly (no height cap): the selector's root is height:100%, so
  // it fills the stretched batch cell and matches the height of the first
  // artifact beside it, scrolling internally when long.
  const selectorProps = {
    titles,
    selectedIndex: selected,
    onSelect: setSelected,
  };
  const selector = renderGroupSelector ? (
    renderGroupSelector(selectorProps)
  ) : (
    <ArtifactGroupSelector {...selectorProps} />
  );

  const batch = (
    <ArtifactBatch
      artifacts={group.artifacts}
      siblings={allArtifacts}
      siblingOffset={offset}
      ctx={ctx}
      leading={selector}
      leadingFlex={wideSelector ? "0 0 46%" : "0 0 25%"}
      leadingMinWidth={wideSelector ? 320 : 220}
    />
  );

  if (!renderStory) return batch;

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      {batch}
      {renderStory(group)}
    </Box>
  );
}

GroupedArtifactsView.propTypes = {
  grouped: PropTypes.object.isRequired,
  ctx: PropTypes.object.isRequired,
  renderGroupSelector: PropTypes.func,
  wideSelector: PropTypes.bool,
  fallbackGroupTitle: PropTypes.func,
  renderStory: PropTypes.func,
  selected: PropTypes.number,
  onSelect: PropTypes.func,
};

/**
 * Render a backend artifact response: every top level item is either a
 * "grouped" selector (`GroupedArtifactsView`) or a plain leaf artifact shown
 * alone at full width.
 *
 * `renderGroupSelector` swaps the group picker for a caller supplied one.
 * `renderStory` appends a caller supplied element below each item (below the
 * selected group, for a grouped one), given that item.
 * `selection` lets the caller own the per item selected group (used to keep it
 * across remounts); omitting it leaves each selector holding its own state.
 */
export default function ArtifactList({
  items,
  ctx = {},
  renderGroupSelector = null,
  wideSelector = false,
  fallbackGroupTitle = null,
  renderStory = null,
  selection = null,
}) {
  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", gap: 3, width: "100%" }}
    >
      {items.map((item, i) => (
        <Box key={i}>
          {item.type === "grouped" ? (
            <GroupedArtifactsView
              grouped={item}
              ctx={ctx}
              renderGroupSelector={renderGroupSelector}
              wideSelector={wideSelector}
              fallbackGroupTitle={fallbackGroupTitle}
              renderStory={renderStory}
              selected={selection ? selection.selectedFor(i) : null}
              onSelect={
                selection ? (value) => selection.onSelect(i, value) : null
              }
            />
          ) : renderStory ? (
            <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
              <ArtifactViewer artifact={item} {...leafProps(item, ctx)} />
              {renderStory(item)}
            </Box>
          ) : (
            <ArtifactViewer artifact={item} {...leafProps(item, ctx)} />
          )}
        </Box>
      ))}
    </Box>
  );
}

ArtifactList.propTypes = {
  items: PropTypes.array.isRequired,
  ctx: PropTypes.object,
  renderGroupSelector: PropTypes.func,
  wideSelector: PropTypes.bool,
  fallbackGroupTitle: PropTypes.func,
  renderStory: PropTypes.func,
  selection: PropTypes.shape({
    selectedFor: PropTypes.func.isRequired,
    onSelect: PropTypes.func.isRequired,
  }),
};
