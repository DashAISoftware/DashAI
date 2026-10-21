import {
  MISSING_VALUE,
  normalizeComponentRef,
  resolveParamValue,
} from "./paramResolution";
import { isPlainObject } from "./traceUtils";

// Guards against pathological/cyclic nested retriever trees.
const MAX_SCHEMA_SUMMARY_DEPTH = 32;

/**
 * Split a dotted summary path into its non-empty segments.
 *
 * @param {*} path - Dotted path (e.g. `embedding_model.model_name`) or an
 *   already-split sequence of segments.
 * @returns {string[]|null} The path segments, or null when the path is invalid.
 */
function toPathSegments(path) {
  if (Array.isArray(path)) {
    const segments = path.filter(
      (segment) => typeof segment === "string" && segment.length > 0,
    );
    return segments.length > 0 ? segments : null;
  }
  if (typeof path !== "string") return null;

  const segments = path
    .split(".")
    .map((segment) => segment.trim())
    .filter(Boolean);
  return segments.length > 0 ? segments : null;
}

/**
 * Recursively build the schema-summary representation of a retriever component
 * from its `metadata.schema_summary_parameters` spec.
 *
 * @param {object|null|undefined} component - Retriever component definition.
 * @param {*} params - Current parameters of the retriever node.
 * @param {function(string): (object|null|undefined)} [resolveComponent] -
 *   Lookup for child component definitions by class name.
 * @param {number} depth - Current recursion depth.
 * @returns {{class: string, params: object, children?: object[]}|null} The
 *   summary, or null when the component cannot be summarised.
 */
function buildSchemaSummaryNode(component, params, resolveComponent, depth) {
  if (depth > MAX_SCHEMA_SUMMARY_DEPTH) return null;
  if (!isPlainObject(component)) return null;
  if (typeof component.name !== "string" || component.name.length === 0) {
    return null;
  }

  const spec = component.metadata?.schema_summary_parameters;
  if (!isPlainObject(spec) || Object.keys(spec).length === 0) return null;

  const summaryParams = {};
  Object.entries(spec).forEach(([label, path]) => {
    if (typeof label !== "string" || label.length === 0) return;

    const segments = toPathSegments(path);
    if (!segments) return;

    let value;
    try {
      value = resolveParamValue(params, segments);
    } catch {
      return;
    }
    if (value === MISSING_VALUE) return;

    const isPrimitive =
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean";
    if (isPrimitive) summaryParams[label] = value;
  });

  const summary = { class: component.name, params: summaryParams };

  const childRefs =
    isPlainObject(params) && Array.isArray(params.children)
      ? params.children
      : [];
  if (childRefs.length === 0) return summary;

  const resolver =
    typeof resolveComponent === "function" ? resolveComponent : null;
  if (!resolver) return summary;

  const childSummaries = [];
  childRefs.forEach((child) => {
    const ref = normalizeComponentRef(child);
    if (!ref) return;

    let childComponent = null;
    try {
      childComponent = resolver(ref.component);
    } catch {
      childComponent = null;
    }

    const childSummary = buildSchemaSummaryNode(
      childComponent,
      ref.params,
      resolver,
      depth + 1,
    );
    if (childSummary) childSummaries.push(childSummary);
  });

  if (childSummaries.length > 0) summary.children = childSummaries;
  return summary;
}

/**
 * Build the schema-summary representation of a retriever component.
 *
 * The summary is declared by the component's
 * `metadata.schema_summary_parameters`, which maps display labels to dotted
 * paths into the raw config params. Nested composite retrievers are walked
 * through `params.children`, resolving each child component by class name.
 *
 * @param {object|null|undefined} component - Retriever component definition.
 * @param {*} params - Current parameters of the retriever node.
 * @param {function(string): (object|null|undefined)} [resolveComponent] -
 *   Lookup for child component definitions by class name.
 * @returns {{class: string, params: object, children?: object[]}|null} The
 *   summary, or null when the component has no (usable) summary spec.
 */
export function buildSchemaSummary(component, params, resolveComponent) {
  try {
    return buildSchemaSummaryNode(component, params, resolveComponent, 0);
  } catch {
    return null;
  }
}

/**
 * Render a node's own schema-summary text as
 * `"<class> · <label> <value> · ..."`. Children are not inlined: the tree
 * renders each of them as its own card.
 *
 * @param {{class: string, params: object}|null|undefined} summary - Schema
 *   summary to render.
 * @param {function(string): string} [translateLabel] - Optional translator for
 *   parameter labels; raw labels are used when it is absent or returns empty.
 * @returns {string|null} The rendered text, or null when the summary is
 *   malformed or has no primitive params to show.
 */
export function renderSchemaSummaryText(summary, translateLabel) {
  if (!isPlainObject(summary)) return null;

  const className = summary.class;
  const params = summary.params;
  if (typeof className !== "string" || className.length === 0) return null;
  if (!isPlainObject(params)) return null;
  if (Object.keys(params).length === 0) return null;

  const parts = [className];
  let primitiveCount = 0;
  Object.entries(params).forEach(([label, value]) => {
    const isPrimitive =
      typeof value === "string" ||
      typeof value === "number" ||
      typeof value === "boolean";
    if (!isPrimitive) return;

    const text = String(value);
    if (text.length === 0) return;

    let displayLabel = label;
    if (typeof translateLabel === "function") {
      try {
        const translated = translateLabel(label);
        if (typeof translated === "string" && translated.length > 0) {
          displayLabel = translated;
        }
      } catch {
        // Fall back to the raw label when translation fails.
      }
    }

    parts.push(`${displayLabel} ${text}`);
    primitiveCount += 1;
  });

  if (primitiveCount === 0) return null;
  return parts.join(" · ");
}

/**
 * Resolve a retriever's schema-summary text from its component definition and
 * current params, falling back to null when no summary is available.
 *
 * @param {object|null|undefined} component - Retriever component definition.
 * @param {*} params - Current parameters of the retriever node.
 * @param {function(string): (object|null|undefined)} [resolveComponent] -
 *   Lookup for child component definitions by class name.
 * @param {function(string): string} [translateLabel] - Optional translator for
 *   parameter labels.
 * @returns {string|null} The rendered summary text, or null when unavailable.
 */
export function resolveRetrieverSchemaSummary(
  component,
  params,
  resolveComponent,
  translateLabel,
) {
  try {
    return renderSchemaSummaryText(
      buildSchemaSummary(component, params, resolveComponent),
      translateLabel,
    );
  } catch {
    return null;
  }
}
