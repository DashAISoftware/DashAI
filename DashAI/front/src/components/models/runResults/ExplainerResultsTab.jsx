import React, { useEffect, useRef } from "react";
import PropTypes from "prop-types";
import { Box, Typography, ToggleButton } from "@mui/material";
import { alpha } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { Virtuoso } from "react-virtuoso";

import PillToggleButtonGroup from "../../shared/PillToggleButtonGroup";
import ExplainersCard from "../../explainers/ExplainersCard";
import LazyExplainerCard from "../../explainers/LazyExplainerCard";
import {
  explainerCacheKey,
  DEFAULT_CARD_HEIGHT,
} from "../../explainers/explainerCache";

/**
 * The Explainability tab: a scope toggle (global / local) over the run's
 * explainer cards. In the full-height detail view the list is virtualized
 * against the outer scroller and a just-created explainer is scrolled into
 * view and flashed; the inline (collapsible card) view renders a plain column.
 */
export default function ExplainerResultsTab({
  activeExplainers,
  explainerFilter,
  setExplainerFilter,
  fillHeight,
  scrollParent,
  explainerDisplayNames,
  cardHeightsRef,
  getCacheEntry,
  updateCacheEntry,
  newExplainerKey,
  setNewExplainerKey,
  highlightedExplainerKey,
  setHighlightedExplainerKey,
  onDelete,
}) {
  const { t } = useTranslation(["models"]);
  const virtuosoRef = useRef(null);

  // Read in the deferred callback so it sees the list after the scope switch.
  const activeExplainersRef = useRef(activeExplainers);
  useEffect(() => {
    activeExplainersRef.current = activeExplainers;
  }, [activeExplainers]);

  // Scroll a new explainer card into view and flash it, like the notebooks
  // view. The delay lets the scope switch settle before scrolling.
  useEffect(() => {
    if (!newExplainerKey) return undefined;
    const scrollTimer = setTimeout(() => {
      const list = activeExplainersRef.current;
      const scope = newExplainerKey.startsWith("global-") ? "global" : "local";
      const id = Number(newExplainerKey.slice(scope.length + 1));
      const index = list.findIndex((e) => e.id === id);
      const targetIndex = index >= 0 ? index : list.length - 1;
      if (virtuosoRef.current && targetIndex >= 0) {
        // align end, not center: a new explainer is appended last, so pinning
        // its bottom lands the scroller fully down; followOutput holds it as
        // the plot loads and the card grows.
        virtuosoRef.current.scrollToIndex({
          index: targetIndex,
          align: "end",
          behavior: "smooth",
        });
      }
      setHighlightedExplainerKey(newExplainerKey);
      setNewExplainerKey(null);
    }, 100);
    return () => clearTimeout(scrollTimer);
  }, [newExplainerKey, setHighlightedExplainerKey, setNewExplainerKey]);

  return (
    <Box sx={{ pb: 4, width: "100%" }}>
      {/* Scope selector pinned to the upper right of the content, so it stays
          visible while the card list scrolls. */}
      <Box
        sx={{
          position: "sticky",
          top: 0,
          zIndex: 2,
          display: "flex",
          justifyContent: "flex-end",
          mb: 2,
        }}
      >
        <PillToggleButtonGroup
          value={explainerFilter}
          onChange={(e, newValue) => {
            if (newValue !== null) setExplainerFilter(newValue);
          }}
          sx={{
            bgcolor: (theme) => alpha(theme.palette.ui.box, 0.8),
            backdropFilter: "blur(8px)",
          }}
        >
          <ToggleButton value="global" sx={{ px: 1.5 }}>
            {t("models:label.globalExplainers")}
          </ToggleButton>
          <ToggleButton value="local" sx={{ px: 1.5 }}>
            {t("models:label.localExplainers")}
          </ToggleButton>
        </PillToggleButtonGroup>
      </Box>

      {activeExplainers.length === 0 ? (
        <Typography
          variant="body2"
          color="text.secondary"
          align="center"
          sx={{ py: 6 }}
        >
          {explainerFilter === "global"
            ? t("models:label.noGlobalExplainersYet")
            : t("models:label.noLocalExplainersYet")}
        </Typography>
      ) : fillHeight ? (
        // Virtualize against the scroller so many plugin cards stay cheap.
        // Keyed on scope so toggling scrolls back to the bottom.
        <Virtuoso
          key={explainerFilter}
          ref={virtuosoRef}
          customScrollParent={scrollParent ?? undefined}
          data={activeExplainers}
          followOutput="smooth"
          initialTopMostItemIndex={Math.max(0, activeExplainers.length - 1)}
          // Overscan margin. Must exceed the card preload margin so the item is
          // in the DOM before the observer shows it. defaultItemHeight seeds
          // the estimate for cards not yet measured.
          increaseViewportBy={{ top: 1000, bottom: 500 }}
          defaultItemHeight={DEFAULT_CARD_HEIGHT}
          itemContent={(index, explainer) => (
            // pb, not flex gap: virtualized items are not flex children. px
            // gives the highlight ring room so the scroller does not clip its
            // sides.
            <Box sx={{ px: 1.5, pb: 2 }}>
              <LazyExplainerCard
                scrollRoot={scrollParent ?? undefined}
                heightsRef={cardHeightsRef}
                cacheKey={explainerCacheKey(explainerFilter, explainer)}
                explainer={explainer}
                scope={explainerFilter}
                displayName={explainerDisplayNames[explainer.explainer_name]}
                onDelete={onDelete}
                cacheEntry={getCacheEntry(
                  explainerCacheKey(explainerFilter, explainer),
                )}
                updateCacheEntry={updateCacheEntry}
                isHighlighted={
                  highlightedExplainerKey ===
                  `${explainerFilter}-${explainer.id}`
                }
              />
            </Box>
          )}
        />
      ) : (
        // Inline view: no bounded scroller, so keep the flex column. px gives
        // the highlight ring room at the sides.
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2, px: 1.5 }}>
          {activeExplainers.map((explainer) => {
            const key = explainerCacheKey(explainerFilter, explainer);
            return (
              <ExplainersCard
                key={`${explainerFilter}-${explainer.id}`}
                explainer={explainer}
                scope={explainerFilter}
                displayName={explainerDisplayNames[explainer.explainer_name]}
                onDelete={onDelete}
                cacheEntry={getCacheEntry(key)}
                onCacheUpdate={(patch) => updateCacheEntry(key, patch)}
                isHighlighted={
                  highlightedExplainerKey ===
                  `${explainerFilter}-${explainer.id}`
                }
                compact
              />
            );
          })}
        </Box>
      )}
    </Box>
  );
}

ExplainerResultsTab.propTypes = {
  activeExplainers: PropTypes.array.isRequired,
  explainerFilter: PropTypes.oneOf(["global", "local"]).isRequired,
  setExplainerFilter: PropTypes.func.isRequired,
  fillHeight: PropTypes.bool,
  scrollParent: PropTypes.instanceOf(Element),
  explainerDisplayNames: PropTypes.object.isRequired,
  cardHeightsRef: PropTypes.shape({ current: PropTypes.object }).isRequired,
  getCacheEntry: PropTypes.func.isRequired,
  updateCacheEntry: PropTypes.func.isRequired,
  newExplainerKey: PropTypes.string,
  setNewExplainerKey: PropTypes.func.isRequired,
  highlightedExplainerKey: PropTypes.string,
  setHighlightedExplainerKey: PropTypes.func.isRequired,
  onDelete: PropTypes.func,
};
