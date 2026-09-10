import { getRetrieverComponents } from "../../../api/rag";

// Cached membership name-sets, populated once by loadRetrieverKinds().
let kinds = null;

/**
 * Load (once) retriever kind membership from the backend component hierarchy:
 * composite (children of CompositeRetriever), keyword (children of
 * SparseRetriever) and embedding (children of DenseEmbedding).
 * @returns {Promise<{composite: Set<string>, keyword: Set<string>, embedding: Set<string>}>}
 */
export async function loadRetrieverKinds() {
  if (kinds) return kinds;
  let composite = [];
  let keyword = [];
  let embedding = [];
  try {
    [composite, keyword, embedding] = await Promise.all([
      getRetrieverComponents("CompositeRetriever"),
      getRetrieverComponents("SparseRetriever"),
      getRetrieverComponents("DenseEmbedding"),
    ]);
  } catch (error) {
    // Degrade gracefully: empty sets mean isComposite/isKeyword/isEmbedding
    // return false and the UI falls back to ungrouped options instead of
    // hanging in a loading state forever.
    console.warn("Failed to load retriever kinds:", error);
  }
  kinds = {
    composite: new Set((composite || []).map((c) => c.name)),
    keyword: new Set((keyword || []).map((c) => c.name)),
    embedding: new Set((embedding || []).map((c) => c.name)),
  };
  return kinds;
}

export function isComposite(name) {
  return Boolean(kinds?.composite?.has(name));
}

export function isKeyword(name) {
  return Boolean(kinds?.keyword?.has(name));
}

export function isEmbedding(name) {
  return Boolean(kinds?.embedding?.has(name));
}
