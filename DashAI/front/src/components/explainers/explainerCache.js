// Stable reference returned for cache misses.
export const EMPTY_EXPLAINER_ENTRY = {
  items: null,
  selectedGroups: {},
};

// Fallback placeholder height before a card has ever been measured.
export const DEFAULT_CARD_HEIGHT = 520;

// Key includes the explainer type and creation time, not just the id: on
// retrain the backend reuses low ids, so a new explainer must not inherit a
// deleted one's cached plot.
export const explainerCacheKey = (scope, e) =>
  `${scope}-${e.id}-${e.explainer_name ?? ""}-${e.created ?? ""}`;

// Reuse the previous object for any explainer whose meaningful fields are
// unchanged, so a poll that returns identical data keeps stable references.
// Without this, every 3s poll hands each card a brand new object, defeating
// LazyExplainerCard's React.memo and re-rendering the whole list (Plotly
// included) on every tick.
export const mergeExplainers = (prev, next) =>
  next.map((e) => {
    const old = prev.find((p) => p.id === e.id);
    return old &&
      old.status === e.status &&
      old.created === e.created &&
      old.explainer_name === e.explainer_name
      ? old
      : e;
  });
