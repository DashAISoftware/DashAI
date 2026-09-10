/**
 * Ordered per-series colors for run/metric comparison charts (session
 * results, live metrics). Interleaves hues instead of listing primary and
 * secondary back-to-back — both are blue, so the first two series were
 * nearly indistinguishable when adjacent.
 */
export const getTraceColors = (theme) => {
  const [green, blueLight, orange, purple, red, teal, brown, blueGrey] = theme
    .palette.chart?.palette || [
    "#66bb6a",
    "#42a5f5",
    "#ff9800",
    "#ab47bc",
    "#ef5350",
    "#26a69a",
    "#8d6e63",
    "#78909c",
  ];

  return [
    theme.palette.primary.main, // blue
    orange,
    green,
    purple,
    red,
    teal,
    brown,
    theme.palette.secondary.main, // blue (darker) — kept far from the first blue
    blueLight, // blue (lighter) — same
    blueGrey,
  ];
};
