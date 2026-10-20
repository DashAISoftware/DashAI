import { resolveLocalizedText } from "../../../utils/localize";

/**
 * Text rendered when a representation placeholder cannot be resolved.
 * @type {string}
 */
export const MISSING_VALUE = "—";

/**
 * Normalise a component reference into a plain `{ component, params }` shape.
 * Supports the form-shaped structure
 * `{ properties: { params: { comp: { component, params } } } }` as well as a
 * plain `{ component, params }` reference.
 *
 * @param {*} value - Candidate component reference.
 * @returns {{component: string, params: object|undefined}|null} The normalised
 *   reference, or null when the value is not a component reference.
 */
export function normalizeComponentRef(value) {
  if (!value || typeof value !== "object") return null;

  const formRef = value.properties?.params?.comp;
  const ref = formRef && typeof formRef === "object" ? formRef : value;
  if (typeof ref.component !== "string" || ref.component.length === 0) {
    return null;
  }
  return { component: ref.component, params: ref.params };
}

/**
 * Render a primitive parameter value as text.
 *
 * @param {*} value - Parameter value.
 * @returns {string} The rendered value, or {@link MISSING_VALUE}.
 */
function renderPrimitive(value) {
  const isPrimitive =
    typeof value === "string" ||
    typeof value === "number" ||
    typeof value === "boolean";
  if (!isPrimitive) return MISSING_VALUE;

  const text = String(value);
  return text.length > 0 ? text : MISSING_VALUE;
}

/**
 * Resolve a dotted parameter path against the current node parameters.
 * A direct component reference renders its class name; a `nested.param` path
 * reads `param` from the nested component stored under `nested`.
 *
 * @param {*} params - Node parameters (may be missing or malformed).
 * @param {string[]} path - Path segments, e.g. `["embedding_model", "model_name"]`.
 * @returns {string} The resolved value, or {@link MISSING_VALUE}.
 */
export function resolveParamValue(params, path) {
  if (!params || typeof params !== "object" || Array.isArray(params)) {
    return MISSING_VALUE;
  }

  const [head, ...rest] = path;
  if (!head) return MISSING_VALUE;

  const raw = params[head];
  if (raw === undefined || raw === null) return MISSING_VALUE;

  const ref = normalizeComponentRef(raw);
  if (rest.length === 0) {
    return ref ? ref.component : renderPrimitive(raw);
  }
  if (!ref) return MISSING_VALUE;

  return resolveParamValue(ref.params, rest);
}

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
