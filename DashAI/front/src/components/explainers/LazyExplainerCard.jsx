import React, { useState, useEffect, useCallback, useRef } from "react";
import PropTypes from "prop-types";
import { Box } from "@mui/material";
import ExplainersCard from "./ExplainersCard";
import { DEFAULT_CARD_HEIGHT } from "./explainerCache";

// IntersectionObserver margin (top right bottom left) for when a card mounts
// its plot. Bigger on top so cards render before entering view when scrolling
// up, so their height has settled and does not cause a correction that tears.
const CARD_PRELOAD_MARGIN = "900px 0px 400px 0px";

/**
 * Renders a card once it nears the viewport, then keeps it mounted (latched),
 * so each plot is created at most once. A box sized to the last measured height
 * holds space until then. Memoized with stable props so unrelated RunResults
 * renders do not restart Plotly. The cache makes the eventual unmount lossless.
 */
const LazyExplainerCard = React.memo(function LazyExplainerCard({
  scrollRoot,
  heightsRef,
  cacheKey,
  explainer,
  scope,
  displayName,
  onDelete,
  cacheEntry,
  updateCacheEntry,
  isHighlighted,
}) {
  const nodeRef = useRef(null);
  const [shown, setShown] = useState(false);

  useEffect(() => {
    const node = nodeRef.current;
    // Once shown, latch: stop observing and never unmount the plot.
    if (!node || shown) return undefined;
    // Give the plot a head start before it scrolls in. Kept within the list's
    // increaseViewportBy so the item is already in the DOM when this fires.
    const observer = new IntersectionObserver(
      ([entry]) => {
        if (entry.isIntersecting) setShown(true);
      },
      { root: scrollRoot ?? null, rootMargin: CARD_PRELOAD_MARGIN },
    );
    observer.observe(node);
    return () => observer.disconnect();
  }, [scrollRoot, shown]);

  useEffect(() => {
    const node = nodeRef.current;
    if (!shown || !node) return undefined;
    const record = () => {
      heightsRef.current[cacheKey] = node.offsetHeight;
    };
    record();
    const observer = new ResizeObserver(record);
    observer.observe(node);
    return () => observer.disconnect();
  }, [shown, cacheKey, heightsRef]);

  const onCacheUpdate = useCallback(
    (patch) => updateCacheEntry(cacheKey, patch),
    [updateCacheEntry, cacheKey],
  );

  const knownHeight = heightsRef.current[cacheKey];
  return (
    <Box
      ref={nodeRef}
      sx={{
        minHeight: shown ? undefined : (knownHeight ?? DEFAULT_CARD_HEIGHT),
        // Own compositor layer so the scroller composites the painted plot
        // instead of repainting heavy Plotly content each frame (which tears).
        // No paint containment: it would clip the highlight ring.
        ...(shown && { transform: "translateZ(0)" }),
      }}
    >
      {shown ? (
        <ExplainersCard
          explainer={explainer}
          scope={scope}
          displayName={displayName}
          onDelete={onDelete}
          cacheEntry={cacheEntry}
          onCacheUpdate={onCacheUpdate}
          isHighlighted={isHighlighted}
          compact
        />
      ) : null}
    </Box>
  );
});

LazyExplainerCard.propTypes = {
  scrollRoot: PropTypes.instanceOf(Element),
  heightsRef: PropTypes.shape({ current: PropTypes.object }).isRequired,
  cacheKey: PropTypes.string.isRequired,
  explainer: PropTypes.object.isRequired,
  scope: PropTypes.string.isRequired,
  displayName: PropTypes.string,
  onDelete: PropTypes.func,
  cacheEntry: PropTypes.object,
  updateCacheEntry: PropTypes.func.isRequired,
  isHighlighted: PropTypes.bool,
};

export default LazyExplainerCard;
