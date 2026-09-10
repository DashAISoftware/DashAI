export const META_THRESHOLDS = Object.freeze({
  COLS: 50,
  ROWS: 100_000,
});

export function estimateTotalRows({
  previewRowCount = 0,
  previewedBytes = 0,
  fileSize = 0,
}) {
  if (!previewRowCount) return 0;
  if (!fileSize || !previewedBytes) return previewRowCount;
  return Math.round(previewRowCount * (fileSize / previewedBytes));
}

export function shouldRecommendDisableMetadata({ colCount = 0, estRows = 0 }) {
  if (colCount > META_THRESHOLDS.COLS) return true;
  if (estRows && estRows > META_THRESHOLDS.ROWS) return true;
  return false;
}
