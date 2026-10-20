/**
 * Pure helpers for the RAG trace/chunks panel. No React imports: these are the
 * data-shaping primitives the panel and its tests rely on.
 */

/**
 * Coerces a possibly-missing list into an array.
 * @param {*} value - The value to coerce.
 * @returns {Array} The value itself when it is an array, otherwise an empty one.
 */
export function asArray(value) {
  return Array.isArray(value) ? value : [];
}

/**
 * Checks whether a value is a non-null, non-array object.
 * @param {*} value - The value to inspect.
 * @returns {boolean} True for plain objects only.
 */
export function isPlainObject(value) {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

/**
 * Checks whether a trace entry carries a retriever object.
 * @param {object} entry - A trace entry.
 * @returns {boolean} True when `entry.retriever` is a plain object.
 */
export function hasObjectRetriever(entry) {
  return isPlainObject(entry?.retriever);
}

/**
 * A trace is query-transformed when more than one query was used, or when the
 * single transformed query differs from the original user message. When the
 * transformation ran but echoed the message back, it is indistinguishable and
 * treated as untransformed.
 * @param {Array<object>} entries - Renderable trace entries.
 * @param {string} [userMessage] - The original user message.
 * @returns {boolean} True when the trace reflects a query transformation.
 */
export function isQueryTransformed(entries, userMessage) {
  if (entries.length <= 1) {
    const only = entries[0];
    return typeof only?.query === "string" && only.query !== userMessage;
  }
  return true;
}

/**
 * Filters a trace list down to the entries that render (object retrievers).
 * @param {*} trace - The raw trace prop.
 * @returns {Array<object>} The renderable trace entries.
 */
export function filterRenderableEntries(trace) {
  return Array.isArray(trace) ? trace.filter(hasObjectRetriever) : [];
}

/**
 * Resolves a document title from a reference entry using the shared fallback
 * chain (title, name, then the localised "Document {{id}}" fallback).
 * @param {object} [info] - The reference entry for the document.
 * @param {number|string} docId - The document identifier.
 * @param {Function} t - i18n translate function.
 * @returns {string} The display title.
 */
export function getDocumentTitle(info, docId, t) {
  if (info?.document_title) return info.document_title;
  if (info?.document_name) return info.document_name;
  if (info?.title) return info.title;
  if (info?.name) return info.name;
  return t("generative:traceChunks.fallbackTitle", { id: docId });
}

/**
 * Builds the human label for a resolved chunk ("Chunk N" or "Chunk N, page P").
 * @param {object} info - A resolved reference entry.
 * @param {Function} t - i18n translate function.
 * @returns {string} The translated chunk label.
 */
export function resolveChunkLabel(info, t) {
  if (info.page != null) {
    return t("traceChunks.chunkLabelWithPage", {
      position: info.document_position,
      page: info.page,
    });
  }
  return t("traceChunks.chunkLabel", { position: info.document_position });
}

/**
 * Groups the final reference chunks by document, preserving first-appearance
 * order, and keeps each chunk's raw ref alongside its payload. Entries whose
 * value is not a plain object are dropped so a corrupt map can never reach the
 * rendering path.
 * @param {object|null} references - Chunk reference map by ref key.
 * @returns {Array<{docId: *, chunks: Array<object>}>} The ordered groups.
 */
export function groupReferencesByDocument(references) {
  if (!isPlainObject(references)) return [];
  const order = [];
  const byDocument = new Map();
  Object.entries(references).forEach(([ref, info]) => {
    if (!isPlainObject(info)) return;
    const docId = info?.document_id;
    if (!byDocument.has(docId)) {
      byDocument.set(docId, []);
      order.push(docId);
    }
    byDocument.get(docId).push({ ref, ...info });
  });
  return order.map((docId) => ({ docId, chunks: byDocument.get(docId) }));
}

/**
 * Collects the chunk refs of a retriever node, recursively and in
 * first-appearance order (the node's own chunks first, then its children).
 * Non-object nodes are skipped and duplicate refs are collapsed.
 * @param {object} node - A retriever node.
 * @returns {string[]} The ordered, de-duplicated refs.
 */
export function collectRefs(node) {
  if (!isPlainObject(node)) return [];
  const refs = [];
  const seen = new Set();
  const visit = (current) => {
    if (!isPlainObject(current)) return;
    asArray(current.chunks).forEach((ref) => {
      if (seen.has(ref)) return;
      seen.add(ref);
      refs.push(ref);
    });
    asArray(current.children).forEach(visit);
  };
  visit(node);
  return refs;
}

/**
 * Summarises the retrieval candidates across every trace entry.
 * @param {Array<object>} entries - Renderable trace entries.
 * @returns {{candidates: string[], perQuery: Array<{count: number}>}}
 *   The ordered union of all refs and, per entry, the recursive union size of
 *   the root node.
 */
export function collectTraceStats(entries) {
  const candidates = [];
  const seen = new Set();
  const perQuery = [];
  asArray(entries).forEach((entry) => {
    const refs = collectRefs(entry?.retriever);
    refs.forEach((ref) => {
      if (seen.has(ref)) return;
      seen.add(ref);
      candidates.push(ref);
    });
    perQuery.push({ count: refs.length });
  });
  return { candidates, perQuery };
}

/**
 * Lists the candidate refs that never reached the final reference map.
 *
 * An absent map (null/undefined) means the reference data itself is missing,
 * so nothing can be claimed about discards; an explicitly empty map means
 * nothing reached the answer, so every candidate counts as discarded.
 * @param {Array<object>} entries - Renderable trace entries.
 * @param {object|null} references - Final chunk reference map, if any.
 * @returns {string[]} Ordered refs present in the trace but not in references.
 */
export function computeDiscardedRefs(entries, references) {
  if (!isPlainObject(references)) return [];
  const { candidates } = collectTraceStats(entries);
  return candidates.filter(
    (ref) => !Object.prototype.hasOwnProperty.call(references, ref),
  );
}

/**
 * Attributes every trace ref to the deepest retriever node(s) that produced it,
 * per query. A ref found by two sibling leaves yields both names; a ref present
 * only at the root yields the root's name. Nodes without a usable name are
 * tracked for depth but contribute no attribution.
 * @param {Array<object>} entries - Renderable trace entries.
 * @returns {Map<string, Array<{queryIndex: number, names: string[]}>>} The
 *   per-ref provenance, with 1-based query indexes in ascending order.
 */
export function computeProvenance(entries) {
  const provenance = new Map();
  asArray(entries).forEach((entry, index) => {
    if (!isPlainObject(entry?.retriever)) return;
    const queryIndex = index + 1;
    const deepest = new Map();
    const visit = (node, depth) => {
      if (!isPlainObject(node)) return;
      asArray(node.chunks).forEach((ref) => {
        const best = deepest.get(ref);
        if (!best || depth > best.depth) {
          deepest.set(ref, { depth, names: new Set() });
        }
        if (
          typeof node.name === "string" &&
          node.name.length > 0 &&
          deepest.get(ref).depth === depth
        ) {
          deepest.get(ref).names.add(node.name);
        }
      });
      asArray(node.children).forEach((child) => visit(child, depth + 1));
    };
    visit(entry.retriever, 0);
    deepest.forEach((value, ref) => {
      const names = [...value.names];
      if (names.length === 0) return;
      const list = provenance.get(ref) ?? [];
      list.push({ queryIndex, names });
      provenance.set(ref, list);
    });
  });
  return provenance;
}
