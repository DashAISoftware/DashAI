import {
  buildYupSchema,
  parseRAGTraceRow,
  preprocessSchema,
  resolveRAGProgressText,
  splitRAGOutputRows,
} from "./utils";

// What pydantic emits for `negative_prompt: Optional[str] = None` next to a
// plain required integer.
const PROPERTIES = {
  negative_prompt: {
    anyOf: [{ type: "string", placeholder: "" }, { type: "null" }],
    default: null,
    title: "Negative Prompt",
  },
  steps: { type: "integer", minimum: 1, title: "Steps" },
} as any;

const schema = buildYupSchema(preprocessSchema(PROPERTIES));

test.each([
  ["empty", ""],
  ["null", null],
  ["missing", undefined],
])("a nullable field accepts a %s value", async (_, value) => {
  await expect(
    schema.validate({ negative_prompt: value, steps: 20 }),
  ).resolves.toBeDefined();
});

test("a field without a default is still required", async () => {
  await expect(schema.validate({ negative_prompt: "" })).rejects.toThrow(
    "Required",
  );
});

const TRACE_DATA = '[{"query":"q1","retriever":{"name":"BM25Retriever"}}]';

// New format: Queries, Dict, Trace, Timings, str (message last).
const NEW_FORMAT = [
  { data_type: "Queries", data: '["q1","q2"]' },
  { data_type: "Dict", data: "{}" },
  { data_type: "Trace", data: TRACE_DATA },
  { data_type: "Timings", data: '{"transformation_ms":0}' },
  { data_type: "str", data: "the answer" },
];

// 3-row format emitted before the Trace row existed.
const NO_TRACE_FORMAT = [
  { data_type: "Queries", data: '["q1","q2"]' },
  { data_type: "Dict", data: "{}" },
  { data_type: "str", data: "the answer" },
];

// Legacy format: str (message first), Dict; no Queries row.
const LEGACY_FORMAT = [
  { data_type: "str", data: "the answer" },
  { data_type: "Dict", data: "{}" },
];

test("splitRAGOutputRows splits the new 5-row format", () => {
  const { queryRow, referenceRow, traceRow, messageRows } =
    splitRAGOutputRows(NEW_FORMAT);
  expect(queryRow).toBe(NEW_FORMAT[0]);
  expect(referenceRow).toBe(NEW_FORMAT[1]);
  expect(traceRow).toBe(NEW_FORMAT[2]);
  // The Timings row is recognised and never leaks into the message rows.
  expect(messageRows).toEqual([NEW_FORMAT[4]]);
});

test("splitRAGOutputRows tolerates the 3-row format without a trace", () => {
  const { queryRow, referenceRow, traceRow, messageRows } =
    splitRAGOutputRows(NO_TRACE_FORMAT);
  expect(queryRow).toBe(NO_TRACE_FORMAT[0]);
  expect(referenceRow).toBe(NO_TRACE_FORMAT[1]);
  expect(traceRow).toBeNull();
  expect(messageRows).toEqual([NO_TRACE_FORMAT[2]]);
});

test("splitRAGOutputRows tolerates the legacy 2-row format", () => {
  const { queryRow, referenceRow, traceRow, messageRows } =
    splitRAGOutputRows(LEGACY_FORMAT);
  expect(queryRow).toBeNull();
  expect(referenceRow).toBe(LEGACY_FORMAT[1]);
  expect(traceRow).toBeNull();
  expect(messageRows).toEqual([LEGACY_FORMAT[0]]);
});

test("splitRAGOutputRows is independent of row order", () => {
  const shuffled = [
    NEW_FORMAT[4],
    NEW_FORMAT[0],
    NEW_FORMAT[3],
    NEW_FORMAT[2],
    NEW_FORMAT[1],
  ];
  const { queryRow, referenceRow, traceRow, messageRows } =
    splitRAGOutputRows(shuffled);
  expect(queryRow).toBe(NEW_FORMAT[0]);
  expect(referenceRow).toBe(NEW_FORMAT[1]);
  expect(traceRow).toBe(NEW_FORMAT[2]);
  expect(messageRows).toEqual([NEW_FORMAT[4]]);
});

test.each([
  ["null", null],
  ["undefined", undefined],
  ["empty", []],
])("splitRAGOutputRows returns an empty result for %s output", (_, output) => {
  expect(splitRAGOutputRows(output as any)).toEqual({
    queryRow: null,
    referenceRow: null,
    traceRow: null,
    messageRows: [],
  });
});

test("splitRAGOutputRows tolerates rows without a data_type and null rows", () => {
  const rows = [{ data: "no type" }, null, undefined, NEW_FORMAT[1]];
  const { queryRow, referenceRow, traceRow, messageRows } = splitRAGOutputRows(
    rows as any,
  );
  expect(queryRow).toBeNull();
  expect(referenceRow).toBe(NEW_FORMAT[1]);
  expect(traceRow).toBeNull();
  expect(messageRows).toEqual([{ data: "no type" }]);
});

test("parseRAGTraceRow parses a valid trace payload", () => {
  expect(parseRAGTraceRow(NEW_FORMAT[2])).toEqual(JSON.parse(TRACE_DATA));
});

test.each([
  ["null row", null],
  ["undefined row", undefined],
  ["missing data", { data_type: "Trace" }],
])("parseRAGTraceRow returns null for a %s", (_, row) => {
  expect(parseRAGTraceRow(row as any)).toBeNull();
});

test("parseRAGTraceRow tolerates malformed JSON without crashing", () => {
  expect(parseRAGTraceRow({ data: "not json{" })).toBeNull();
});

describe("resolveRAGProgressText", () => {
  test.each([
    ["null", null],
    ["undefined", undefined],
  ])("returns null for %s progress", (_, progress) => {
    expect(resolveRAGProgressText(progress as any)).toBeNull();
  });

  test.each([
    ["missing stage", {}],
    ["unknown stage", { stage: "unknown" }],
  ])("returns null for a payload with a %s", (_, progress) => {
    expect(resolveRAGProgressText(progress as any)).toBeNull();
  });

  test("maps the transforming stage to its i18n key", () => {
    expect(resolveRAGProgressText({ stage: "transforming" })).toEqual({
      key: "generative:rag.chatProgress.transformingQuery",
    });
  });

  test("maps the retrieving stage to its i18n key with joined queries", () => {
    expect(
      resolveRAGProgressText({ stage: "retrieving", queries: ["a", "b"] }),
    ).toEqual({
      key: "generative:rag.chatProgress.searchingSources",
      values: { queries: "a; b" },
    });
  });

  test.each([
    ["missing queries", { stage: "retrieving" }],
    ["empty queries", { stage: "retrieving", queries: [] }],
    ["non-array queries", { stage: "retrieving", queries: "a; b" }],
    ["blank-string queries", { stage: "retrieving", queries: [""] }],
  ])("returns null for retrieving with %s", (_, progress) => {
    expect(resolveRAGProgressText(progress as any)).toBeNull();
  });

  test("maps the generating stage to its i18n key", () => {
    expect(resolveRAGProgressText({ stage: "generating" })).toEqual({
      key: "generative:rag.chatProgress.generatingAnswer",
    });
  });
});
