/**
 * Build the relayout payload that resets a figure's cartesian axes.
 *
 * Only axes present in the figure's computed layout are included. Non
 * cartesian figures (parallel coordinates, pie, polar) carry no `xaxis` or
 * `yaxis` there, and asking Plotly to autorange an axis it does not have
 * throws inside its own `relayout` while reading `_inputDomain`.
 *
 * @param {object} fullLayout The plot element's `_fullLayout`.
 * @returns {object|null} The relayout payload, or null when the figure has no
 *   cartesian axis to reset.
 */
export function buildAxisResetUpdate(fullLayout) {
  const update = {};
  if (fullLayout?.xaxis) update["xaxis.autorange"] = true;
  if (fullLayout?.yaxis) update["yaxis.autorange"] = true;
  return Object.keys(update).length > 0 ? update : null;
}
