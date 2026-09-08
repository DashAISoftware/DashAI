/**
 * Replace one leaf artifact's payload in a fetched artifact list.
 *
 * Saving a plot edit persists it on the backend, but the list the frontend
 * already holds still carries the computed figure. Anything that re-reads that
 * list, such as a grouped selector switching instance and back, would show the
 * pre-edit plot. Folding the saved figure in keeps the two in step without a
 * refetch.
 *
 * Leaves nested inside a "grouped" selector are matched by their stamped index
 * exactly like top level ones, which is how the backend keys overrides too.
 *
 * @param {Array} items     Artifact/grouped dicts as returned by the backend.
 * @param {number} index    Stamped index of the leaf to replace.
 * @param {string} payload  The edited plotly figure, JSON stringified.
 * @returns {Array}         A new list; inputs are not mutated.
 */
export function patchArtifactPayload(items, index, payload) {
  const patchLeaf = (leaf) =>
    leaf.index === index ? { ...leaf, payload, overridden: true } : leaf;

  return (items ?? []).map((item) => {
    if (item.type === "grouped") {
      return {
        ...item,
        groups: (item.groups ?? []).map((group) => ({
          ...group,
          artifacts: (group.artifacts ?? []).map(patchLeaf),
        })),
      };
    }
    return patchLeaf(item);
  });
}
