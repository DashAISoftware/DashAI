import { getComponents } from "../../../../api/component";
import { formattedSubform, resolveDefaults } from "../../../../utils/schema";

const COMPONENT_REF_TYPE = "object";

/**
 * Merge the params declared in a component field's schema placeholder into the
 * formatted default value for that field.
 *
 * The shared formatter builds a component field's defaults from the *nested*
 * component's schema and ignores the placeholder `params`. That is fine for
 * most fields, but RAG uses the placeholder to override one nested value (the
 * retrieval LLM's context window). This RAG-local step restores that intent
 * without changing the shared formatter.
 *
 * The merge is schema-driven: any component field with a resolvable default
 * participates, so no retriever or parameter name is hardcoded.
 *
 * @param {object} defaults - Values returned by the shared `resolveDefaults`.
 * @param {object} [schema] - Raw component schema from the components API.
 * @returns {object} A new defaults object with the placeholder params applied.
 */
export function applyPlaceholderParams(defaults, schema) {
  if (!schema?.properties) return defaults;

  const next = { ...defaults };
  for (const [key, property] of Object.entries(schema.properties)) {
    const isComponentRef =
      property?.type === COMPONENT_REF_TYPE && Boolean(property.parent);
    const placeholder = property?.placeholder;
    if (!isComponentRef || !placeholder?.component) continue;

    const current = next[key]?.properties?.params?.comp;
    next[key] = formattedSubform({
      parent: property.parent,
      model: current?.component ?? placeholder.component,
      params: {
        ...(current?.params ?? {}),
        ...(placeholder.params ?? {}),
      },
    });
  }
  return next;
}

/**
 * Resolve a retriever's default values, applying the params its schema
 * placeholders declare for nested component fields.
 *
 * `resolveDefaults` remains the source of the form-shaped defaults; this
 * wrapper only augments them with the placeholder params the shared formatter
 * cannot see. If the raw schema cannot be fetched, the shared defaults are
 * returned unchanged.
 *
 * @param {string} modelName - Registered retriever component name.
 * @returns {Promise<object>} The form-shaped defaults for the retriever.
 */
export async function resolveRetrieverDefaults(modelName) {
  const defaults = await resolveDefaults(modelName);
  try {
    const response = await getComponents({ model: modelName });
    const component = Array.isArray(response) ? response[0] : response;
    return applyPlaceholderParams(defaults, component?.schema);
  } catch (error) {
    console.warn(
      `[resolveRetrieverDefaults] Failed to read placeholders for ${modelName}:`,
      error,
    );
    return defaults;
  }
}
