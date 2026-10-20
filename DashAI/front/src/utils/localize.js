/**
 * Reduce a locale code to its base language: `es-CL` -> `es`, `zh-Hans` -> `zh`.
 * @param {*} language - Locale code or i18next instance.
 * @returns {string} The normalized base language, or an empty string.
 */
function normalizeLanguage(language) {
  if (typeof language !== "string") return "";
  return language.split(/[-,;]/)[0].trim().toLowerCase();
}

/**
 * Resolve a plain string or multilingual object for the active UI language.
 * Falls back to English, then Spanish when the active language is missing.
 *
 * @param {string|object|null|undefined} value - Plain string or multilingual
 *   object (e.g. `{ en, es, pt, de, zh }`).
 * @param {object|string} i18n - i18next instance (with a `language` property)
 *   or a language code.
 * @returns {string|null} The resolved text, or null when none is available.
 */
export function resolveLocalizedText(value, i18n) {
  if (typeof value === "string") return value;
  if (!value || typeof value !== "object") return null;

  const language = normalizeLanguage(
    typeof i18n === "string" ? i18n : i18n?.language,
  );
  for (const key of [language, "en", "es"]) {
    if (key && typeof value[key] === "string" && value[key]) return value[key];
  }

  const fallback = Object.values(value).find(
    (entry) => typeof entry === "string" && entry,
  );
  return fallback || null;
}
