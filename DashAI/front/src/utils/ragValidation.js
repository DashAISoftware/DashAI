/**
 * Validates that a RAG model configuration has complete parameters.
 * A model config is `{ component: string, params: object }`.
 *
 * Checks:
 * - component is a non-empty string
 * - params is a non-empty object (at least 1 key)
 * - Recursively checks sub-components in:
 *     - Canonical format: `{ component: "X", params: {...} }`
 *     - Properties wrapper format: `{ properties: { component, params: { comp: { component, params } } } }`
 *     - Arrays of sub-configs (composite retriever `children`)
 * - Guards against null params
 *
 * @param {object}   model - The model config { component, params }.
 * @param {Function} t     - i18n translate function.
 * @returns {{ valid: boolean, errors: string[] }} Validation result with translated error messages.
 */
export function validateModelConfig(model, t) {
  const errors = [];

  if (
    !model ||
    !model.component ||
    typeof model.component !== "string" ||
    model.component.trim() === ""
  ) {
    errors.push(t("generative:rag.validation.modelComponentMissing"));
    return { valid: false, errors };
  }

  const params = model.params;
  if (
    !params ||
    typeof params !== "object" ||
    Array.isArray(params) ||
    Object.keys(params).length === 0
  ) {
    errors.push(
      t("generative:rag.validation.modelParamsIncomplete", {
        model: model.component,
      }),
    );
    return { valid: false, errors };
  }

  _checkSubComponents(params, t, errors);

  return { valid: errors.length === 0, errors };
}

/**
 * Recursively inspect sub-component values for empty params or
 * empty children arrays in composite retrievers.
 *
 * @param {object}   value  - The params dict or sub-config value to inspect.
 * @param {Function} t      - i18n translate function.
 * @param {string[]} errors - Accumulator for translated error messages.
 */
function _checkSubComponents(value, t, errors) {
  if (!value || typeof value !== "object") return;

  for (const [key, v] of Object.entries(value)) {
    // Skip scalar values and nulls
    if (!v || typeof v !== "object") continue;

    // ── Arrays (e.g. composite retriever children) ──
    if (Array.isArray(v)) {
      for (let i = 0; i < v.length; i++) {
        const item = v[i];
        if (item && typeof item === "object") {
          if (item.component && _isEmptyParams(item.params)) {
            errors.push(
              t("generative:rag.validation.modelParamsIncomplete", {
                model: item.component,
              }),
            );
          } else if (item.component) {
            // Recurse into child's own params
            if (
              item.params &&
              typeof item.params === "object" &&
              !Array.isArray(item.params)
            ) {
              _checkSubComponents(item.params, t, errors);
            }
          }
        }
      }
      continue;
    }

    // ── Properties wrapper format ──
    if (v.properties) {
      const comp = v.properties?.params?.comp;
      if (comp && comp.component && comp.params !== undefined) {
        if (_isEmptyParams(comp.params)) {
          errors.push(
            t("generative:rag.validation.modelParamsIncomplete", {
              model: comp.component,
            }),
          );
        } else if (
          comp.params &&
          typeof comp.params === "object" &&
          !Array.isArray(comp.params)
        ) {
          _checkSubComponents(comp.params, t, errors);
        }
      }
      continue;
    }

    // ── Canonical format { component, params } ──
    if (v.component) {
      if (_isEmptyParams(v.params)) {
        errors.push(
          t("generative:rag.validation.modelParamsIncomplete", {
            model: v.component,
          }),
        );
      } else if (
        v.params &&
        typeof v.params === "object" &&
        !Array.isArray(v.params)
      ) {
        _checkSubComponents(v.params, t, errors);
      }
      continue;
    }

    // ── Nested plain object — recurse ──
    if (!Array.isArray(v)) {
      _checkSubComponents(v, t, errors);
    }
  }
}

/**
 * Returns true when `p` is missing, null, or an empty object.
 * Arrays are considered populated (empty arrays are valid configs).
 */
function _isEmptyParams(p) {
  if (p === null || p === undefined) return true;
  if (typeof p !== "object") return true;
  if (Array.isArray(p)) return false;
  return Object.keys(p).length === 0;
}
