/**
 * Generic component-reference and parameter resolution helpers shared by the
 * retriever representation and schema-summary modules.
 */

/**
 * Text rendered when a representation placeholder cannot be resolved.
 * @type {string}
 */
export const MISSING_VALUE = "—";

/**
 * Checks whether a value is a `{component, params}` reference. Mirrors the
 * backend predicate: the value must carry a `component` key holding a
 * non-empty string and a `params` key.
 *
 * @param {*} value - Candidate component reference.
 * @returns {boolean} True for a valid component reference.
 */
function isComponentRef(value) {
  return (
    Boolean(value) &&
    typeof value === "object" &&
    !Array.isArray(value) &&
    Object.prototype.hasOwnProperty.call(value, "params") &&
    typeof value.component === "string" &&
    value.component.length > 0
  );
}

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
  if (!isComponentRef(ref)) return null;
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
 * @param {string|string[]|undefined} path - Dotted path or path segments, e.g.
 *   `"embedding_model.model_name"` or `["embedding_model", "model_name"]`.
 * @returns {string} The resolved value, or {@link MISSING_VALUE}.
 */
export function resolveParamValue(params, path) {
  if (!params || typeof params !== "object" || Array.isArray(params)) {
    return MISSING_VALUE;
  }

  const segments = Array.isArray(path)
    ? path
    : String(path ?? "")
        .split(".")
        .filter(Boolean);
  const [head, ...rest] = segments;
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
