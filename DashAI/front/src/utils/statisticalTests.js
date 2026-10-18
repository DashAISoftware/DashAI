/**
 * Generate hypothesis test interpretation message based on test results and language
 * @param {boolean} significant - Whether the result is significant
 * @param {number} pValue - The p-value from the test
 * @param {number} alpha - The significance level
 * @param {Function} t - i18next translation function
 * @returns {string} Localized hypothesis decision message
 */
export const getHypothesisDecisionMessage = (significant, pValue, alpha, t) => {
  if (!t) return "";

  const decision = significant
    ? t("models:message.hypothesis_reject")
    : t("models:message.hypothesis_failToReject");

  return t("models:message.hypothesisDecision", {
    decision,
    pValue,
    alpha,
  });
};

/**
 * Format a p-value for display.
 * Uses scientific notation for very small values and a fixed 4-decimal
 * representation otherwise. Returns an em dash for missing/invalid values.
 *
 * @param {number|null|undefined} p
 * @returns {string}
 */
export const formatPValue = (p) => {
  if (p === null || p === undefined || isNaN(p)) return "—";
  if (p < 0.0001) return p.toExponential(2);
  return p.toFixed(4);
};

/**
 * Format a test statistic for display.
 * The backend sends infinite statistics as the strings "Infinity" /
 * "-Infinity" (JSON has no infinity), shown here as ∞ / -∞. Returns an em
 * dash for missing/invalid values.
 *
 * @param {number|string|null|undefined} value
 * @returns {string}
 */
export const formatStatistic = (value) => {
  if (value === null || value === undefined) return "—";
  const statistic = Number(value);
  if (isNaN(statistic)) return "—";
  if (statistic === Infinity) return "∞";
  if (statistic === -Infinity) return "-∞";
  return statistic.toFixed(4);
};
