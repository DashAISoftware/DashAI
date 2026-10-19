import {
  isPlainObject,
  hasObjectRetriever,
  isQueryTransformed,
  filterRenderableEntries,
  groupReferencesByDocument,
  getDocumentTitle,
  collectRefs,
  collectTraceStats,
  computeDiscardedRefs,
  computeProvenance,
} from "./traceUtils";

const NESTED = {
  name: "ParallelRetriever",
  chunks: ["root_0"],
  children: [
    { name: "BM25Retriever", chunks: ["b_1", "shared_2"] },
    {
      name: "RerankRetriever",
      chunks: [],
      children: [{ name: "DenseRetriever", chunks: ["shared_2", "d_3"] }],
    },
  ],
};

describe("object guards", () => {
  test("isPlainObject only accepts non-null, non-array objects", () => {
    expect(isPlainObject({})).toBe(true);
    expect(isPlainObject([])).toBe(false);
    expect(isPlainObject(null)).toBe(false);
    expect(isPlainObject(undefined)).toBe(false);
    expect(isPlainObject("x")).toBe(false);
  });

  test("hasObjectRetriever requires a plain-object retriever", () => {
    expect(hasObjectRetriever({ retriever: { name: "x" } })).toBe(true);
    expect(hasObjectRetriever({ retriever: "x" })).toBe(false);
    expect(hasObjectRetriever({})).toBe(false);
    expect(hasObjectRetriever(null)).toBe(false);
  });

  test("filterRenderableEntries keeps only object retrievers and rejects non-arrays", () => {
    const entries = [{ retriever: {} }, { retriever: 1 }, null, "bad"];
    expect(filterRenderableEntries(entries)).toEqual([{ retriever: {} }]);
    expect(filterRenderableEntries(null)).toEqual([]);
    expect(filterRenderableEntries("oops")).toEqual([]);
  });

  test("isQueryTransformed compares the single query against the message", () => {
    expect(isQueryTransformed([{ query: "x" }], "x")).toBe(false);
    expect(isQueryTransformed([{ query: "y" }], "x")).toBe(true);
    expect(isQueryTransformed([{ query: "x" }, { query: "x" }], "x")).toBe(
      true,
    );
    expect(isQueryTransformed([], "x")).toBe(false);
  });
});

describe("collectRefs", () => {
  test("walks nested composites in first-appearance order and de-duplicates", () => {
    expect(collectRefs(NESTED)).toEqual(["root_0", "b_1", "shared_2", "d_3"]);
  });

  test("returns an empty list for malformed nodes", () => {
    expect(collectRefs(null)).toEqual([]);
    expect(collectRefs("nope")).toEqual([]);
    expect(collectRefs({ children: [null, "bad", { chunks: ["a"] }] })).toEqual(
      ["a"],
    );
  });
});

describe("collectTraceStats", () => {
  test("unions candidates across queries and reports per-query counts", () => {
    const entries = [
      { query: "a", retriever: NESTED },
      {
        query: "b",
        retriever: { name: "BM25Retriever", chunks: ["b_1", "q2_0"] },
      },
      { query: "bad", retriever: 42 },
    ];
    const stats = collectTraceStats(entries);
    expect(stats.candidates).toEqual([
      "root_0",
      "b_1",
      "shared_2",
      "d_3",
      "q2_0",
    ]);
    expect(stats.perQuery).toEqual([{ count: 4 }, { count: 2 }, { count: 0 }]);
  });
});

describe("computeDiscardedRefs", () => {
  test("returns candidates missing from the reference map, in order", () => {
    const entries = [{ query: "a", retriever: NESTED }];
    expect(computeDiscardedRefs(entries, { root_0: {}, d_3: {} })).toEqual([
      "b_1",
      "shared_2",
    ]);
  });

  test("is defensive when the reference map is missing", () => {
    const entries = [{ query: "a", retriever: NESTED }];
    expect(computeDiscardedRefs(entries, null)).toEqual([]);
    expect(computeDiscardedRefs(entries, undefined)).toEqual([]);
  });

  test("an explicitly empty map discards every candidate and ignores prototype keys", () => {
    const entries = [
      { query: "a", retriever: { name: "R", chunks: ["x", "toString"] } },
    ];
    expect(computeDiscardedRefs(entries, {})).toEqual(["x", "toString"]);
  });
});

describe("computeProvenance", () => {
  test("attributes each ref to the deepest node(s) within every query", () => {
    const provenance = computeProvenance([
      { query: "a", retriever: NESTED },
      {
        query: "b",
        retriever: { name: "BM25Retriever", chunks: ["b_1", "q2_0"] },
      },
    ]);

    expect(provenance.get("root_0")).toEqual([
      { queryIndex: 1, names: ["ParallelRetriever"] },
    ]);
    expect(provenance.get("shared_2")).toEqual([
      { queryIndex: 1, names: ["DenseRetriever"] },
    ]);
    expect(provenance.get("b_1")).toEqual([
      { queryIndex: 1, names: ["BM25Retriever"] },
      { queryIndex: 2, names: ["BM25Retriever"] },
    ]);
    expect(provenance.get("q2_0")).toEqual([
      { queryIndex: 2, names: ["BM25Retriever"] },
    ]);
  });

  test("lists every sibling that shares the deepest ref", () => {
    const siblings = {
      name: "ParallelRetriever",
      chunks: [],
      children: [
        { name: "A", chunks: ["x"] },
        { name: "B", chunks: ["x"] },
      ],
    };
    const provenance = computeProvenance([{ query: "q", retriever: siblings }]);
    expect(provenance.get("x")).toEqual([{ queryIndex: 1, names: ["A", "B"] }]);
  });

  test("skips malformed children and malformed entries", () => {
    const provenance = computeProvenance([
      {
        query: "q",
        retriever: {
          name: "Root",
          chunks: ["r"],
          children: [null, "bad", { name: "Child", chunks: ["r"] }],
        },
      },
      { query: "bad", retriever: "not-an-object" },
    ]);
    expect(provenance.get("r")).toEqual([{ queryIndex: 1, names: ["Child"] }]);
  });

  test("unnamed nodes win on depth but contribute no attribution", () => {
    const provenance = computeProvenance([
      {
        query: "q",
        retriever: {
          name: "Root",
          chunks: [],
          children: [{ chunks: ["x"] }, { name: "Deep", chunks: ["y"] }],
        },
      },
    ]);
    // "x" only ever appears under an unnamed node: no attribution at all.
    expect(provenance.has("x")).toBe(false);
    expect(provenance.get("y")).toEqual([{ queryIndex: 1, names: ["Deep"] }]);
  });
});

describe("groupReferencesByDocument + getDocumentTitle", () => {
  const references = {
    "1_0": {
      document_id: 1,
      document_name: "A",
      document_position: 1,
      text: "a",
    },
    "2_0": { document_id: 2, name: "B", document_position: 1, text: "b" },
    "1_1": {
      document_id: 1,
      document_title: "A2",
      document_position: 2,
      text: "c",
    },
  };

  test("groups chunks by document preserving first-appearance order", () => {
    const groups = groupReferencesByDocument(references);
    expect(groups.map((group) => group.docId)).toEqual([1, 2]);
    expect(groups[0].chunks).toHaveLength(2);
    expect(groups[0].chunks.map((chunk) => chunk.ref)).toEqual(["1_0", "1_1"]);
  });

  test("resolves titles through the fallback chain", () => {
    const groups = groupReferencesByDocument(references);
    const t = (key, opts) => `${key}:${opts?.id ?? ""}`;
    expect(getDocumentTitle(groups[0].chunks[0], 1, t)).toBe("A");
    expect(getDocumentTitle(groups[1].chunks[0], 2, t)).toBe("B");
    expect(getDocumentTitle({}, 9, t)).toBe(
      "generative:traceChunks.fallbackTitle:9",
    );
  });
});
