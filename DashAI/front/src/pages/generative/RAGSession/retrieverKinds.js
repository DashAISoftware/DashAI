import { getRetrieverComponents } from "../../../api/rag";

// Cached membership name-sets, populated once by loadRetrieverKinds().
let kinds = null;

/**
 * Load (once) retriever kind membership from the backend component hierarchy:
 * composite (children of CompositeRetriever) and embedding (children of
 * TextEmbeddingConverter).
 * @returns {Promise<{composite: Set<string>, embedding: Set<string>}>}
 */
export async function loadRetrieverKinds() {
  if (kinds) return kinds;
  let composite = [];
  let embedding = [];
  try {
    [composite, embedding] = await Promise.all([
      getRetrieverComponents("CompositeRetriever"),
      getRetrieverComponents("TextEmbeddingConverter"),
    ]);
  } catch (error) {
    // Degrade gracefully: empty sets mean isComposite/isEmbedding
    // return false and the UI falls back to ungrouped options instead of
    // hanging in a loading state forever.
    console.warn("Failed to load retriever kinds:", error);
  }
  kinds = {
    composite: new Set((composite || []).map((c) => c.name)),
    embedding: new Set((embedding || []).map((c) => c.name)),
  };
  return kinds;
}

export function isComposite(name) {
  return Boolean(kinds?.composite?.has(name));
}

export function isEmbedding(name) {
  return Boolean(kinds?.embedding?.has(name));
}

/**
 * Returns the backend category a retriever is grouped under.
 * @param {object} retriever - A retriever component from the registry.
 * @param {string} fallback - Label used when the retriever declares none.
 * @returns {string} The localized category.
 */
export function retrieverCategory(retriever, fallback) {
  return retriever?.metadata?.category || fallback;
}

/**
 * Orders retrievers so each category is contiguous, keeping the categories
 * in the order they first appear, as grouped autocompletes require.
 * @param {Array<object>} retrievers - Retriever components.
 * @param {string} fallback - Category for retrievers that declare none.
 * @returns {Array<object>} A new, grouped array.
 */
export function sortByCategory(retrievers, fallback) {
  const order = [];
  for (const retriever of retrievers) {
    const category = retrieverCategory(retriever, fallback);
    if (!order.includes(category)) order.push(category);
  }
  return [...retrievers].sort(
    (a, b) =>
      order.indexOf(retrieverCategory(a, fallback)) -
      order.indexOf(retrieverCategory(b, fallback)),
  );
}
