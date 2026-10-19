/**
 * Translate a structure message from the backend's infer_structure
 * (`{code, params}`) into user-facing text, from `models:structure.<code>`.
 *
 * A few codes need their params shaped first: a cardinality error names
 * whichever bound was broken, and any list (accepted types, dropped
 * columns) is joined into readable text.
 *
 * @param {Function} t the i18next translation function
 * @param {{code: string, params?: object}} message
 * @returns {string}
 */
export function formatStructureMessage(t, message) {
  if (!message) return "";
  const params = { ...(message.params || {}) };
  let key = message.code;
  if (key === "cardinality") {
    const tooFew = params.min != null && params.selected < params.min;
    key = tooFew ? "cardinalityMin" : "cardinalityMax";
  }
  Object.keys(params).forEach((name) => {
    if (Array.isArray(params[name])) {
      params[name] = params[name].join(", ");
    }
  });
  return t(`models:structure.${key}`, {
    ...params,
    interpolation: { escapeValue: false },
  });
}
