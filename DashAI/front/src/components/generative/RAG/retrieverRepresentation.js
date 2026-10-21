import { resolveLocalizedText } from "../../../utils/localize";
import {
  MISSING_VALUE,
  normalizeComponentRef,
  resolveParamValue,
} from "./paramResolution";

// Re-export the generic resolution helpers for backward compatibility.
export { MISSING_VALUE, normalizeComponentRef, resolveParamValue };

/**
 * Substitute every `{...}` placeholder in a representation template.
 *
 * @param {string} template - Representation template.
 * @param {*} params - Node parameters used to resolve placeholders.
 * @returns {string|null} The interpolated text, or null when the template is
 *   missing, interpolation fails unexpectedly, or no placeholder resolves
 *   (so an all-em-dash caption never hides the component description).
 */
export function interpolateRepresentation(template, params) {
  if (typeof template !== "string" || template.length === 0) return null;

  try {
    let sawPlaceholder = false;
    let resolvedPlaceholder = false;
    const rendered = template.replace(/\{([^{}]+)\}/g, (_match, token) => {
      sawPlaceholder = true;
      const path = token.trim().split(".").filter(Boolean);
      const value =
        path.length > 0 ? resolveParamValue(params, path) : MISSING_VALUE;
      if (value !== MISSING_VALUE) resolvedPlaceholder = true;
      return value;
    });

    return !sawPlaceholder || resolvedPlaceholder ? rendered : null;
  } catch {
    return null;
  }
}

/**
 * Resolve a retriever's declarative representation against its current params.
 * The template lives in `component.metadata.representation` and may be a plain
 * string or a multilingual object.
 *
 * @param {object|null|undefined} component - Retriever component definition.
 * @param {*} params - Current parameters of the retriever node.
 * @param {object|string} i18n - i18next instance or language code.
 * @returns {string|null} The rendered representation, or null when the
 *   component has no template or none of its placeholders resolves.
 */
export function resolveRetrieverRepresentation(component, params, i18n) {
  try {
    const template = resolveLocalizedText(
      component?.metadata?.representation,
      i18n,
    );
    if (!template) return null;
    return interpolateRepresentation(template, params);
  } catch {
    return null;
  }
}
