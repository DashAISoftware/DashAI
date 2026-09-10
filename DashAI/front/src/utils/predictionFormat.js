export function getTargetDecimals(sample, targetColumn) {
  if (!sample || !targetColumn || !sample[targetColumn]) return null;
  const values = sample[targetColumn];
  let maxDecimals = 0;
  for (const val of values) {
    if (val == null || typeof val !== "number") continue;
    const str = String(val);
    const dot = str.indexOf(".");
    if (dot !== -1) maxDecimals = Math.max(maxDecimals, str.length - dot - 1);
  }
  return maxDecimals;
}

export function formatPredictionRows(rows, targetColumn, targetDecimals) {
  if (!rows.length || targetColumn == null) return rows;
  return rows.map((row) => {
    const val = row[targetColumn];
    if (typeof val !== "number") return row;
    return {
      ...row,
      [targetColumn]:
        targetDecimals !== null
          ? val.toFixed(targetDecimals)
          : String(parseFloat(val.toPrecision(12))),
    };
  });
}
