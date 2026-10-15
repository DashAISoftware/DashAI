import React from "react";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SnackbarProvider } from "notistack";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import TraceChunksModal from "./TraceChunksModal";

// Exact English strings the real locale bundle must expose under
// `generative.traceChunks`; the suite relies on the shipped translations.
const EN = {
  title: "Message sources",
  transformedLabel: "The sources provided by each query were:",
  allQueriesChip: "All",
  discarded:
    "This chunk was discarded: it did not reach the end of the pipeline.",
  emptyState: "No chunks were retrieved for this response.",
};

const REFERENCES = {
  "1_0": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 3,
    page: 2,
    text: "alpha text",
  },
  "2_1": {
    document_id: 2,
    document_name: "Beta.pdf",
    document_position: 7,
    page: null,
    text: "beta text",
  },
  "1_3": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 5,
    page: 4,
    text: "gamma text",
  },
};

const TRACE = [
  {
    query: "what is alpha",
    retriever: {
      name: "ParallelRetriever",
      chunks: ["1_0", "9_9"],
      children: [
        { name: "BM25Retriever", chunks: ["1_0"] },
        { name: "TFIDFRetriever", chunks: ["9_9"] },
      ],
    },
  },
  {
    query: "what is beta",
    retriever: { name: "BM25Retriever", chunks: ["2_1"] },
  },
];

function renderModal(overrides = {}) {
  const props = {
    open: true,
    onClose: jest.fn(),
    userMessage: "What is alpha?",
    trace: TRACE,
    references: REFERENCES,
    ...overrides,
  };
  return renderWithProviders(
    <SnackbarProvider>
      <TraceChunksModal {...props} />
    </SnackbarProvider>,
  );
}

function tree() {
  return screen.getByTestId("trace-tree");
}

function selector() {
  return screen.getByTestId("query-selector");
}

function chipLabels() {
  return within(selector())
    .getAllByTestId("query-chip")
    .map((chip) => chip.textContent);
}

test("(a) groups final chunks by document with centered headings and count lines", () => {
  renderModal();

  const doc1 = screen.getByTestId("doc-group-1");
  expect(within(doc1).getByText("Alpha.pdf")).toBeInTheDocument();
  expect(
    within(doc1).getByText(
      "This document provided 2 chunks for this response:",
    ),
  ).toBeInTheDocument();

  const doc2 = screen.getByTestId("doc-group-2");
  expect(within(doc2).getByText("Beta.pdf")).toBeInTheDocument();
  expect(
    within(doc2).getByText("This document provided 1 chunk for this response:"),
  ).toBeInTheDocument();
});

test("(b) the title is always the translated static title", () => {
  const { unmount } = renderModal();
  expect(screen.getByTestId("trace-chunks-title")).toHaveTextContent(EN.title);
  unmount();

  const singleDoc = {
    "1_0": REFERENCES["1_0"],
    "1_3": REFERENCES["1_3"],
  };
  renderModal({ references: singleDoc });
  expect(screen.getByTestId("trace-chunks-title")).toHaveTextContent(EN.title);
});

test("(c) the user message renders inside a bubble and nowhere else", () => {
  renderModal();

  const box = screen.getByTestId("user-message-box");
  expect(within(box).getByText("What is alpha?")).toBeInTheDocument();
  expect(screen.getAllByText("What is alpha?")).toHaveLength(1);
});

test("(d) a single untransformed query hides the label and selector", () => {
  renderModal({
    userMessage: "what is alpha",
    trace: [{ query: "what is alpha", retriever: TRACE[0].retriever }],
  });

  expect(screen.queryByText(EN.transformedLabel)).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();
  expect(within(tree()).getByText("ParallelRetriever")).toBeInTheDocument();
});

test("(e) a single transformed query shows the label and one 'Query 1' chip", () => {
  renderModal({
    trace: [{ query: "a different query", retriever: TRACE[0].retriever }],
  });

  expect(screen.getByText(EN.transformedLabel)).toBeInTheDocument();
  const chips = within(selector()).getAllByTestId("query-chip");
  expect(chips).toHaveLength(1);
  expect(chips[0]).toHaveTextContent("Query 1");
  expect(
    within(selector()).queryByText(EN.allQueriesChip),
  ).not.toBeInTheDocument();
  expect(within(tree()).getByText("ParallelRetriever")).toBeInTheDocument();
  expect(screen.getByTestId("selected-query-text")).toHaveTextContent(
    "a different query",
  );
});

test("(f) the multi-query selector offers All first and defaults to both trees", async () => {
  renderModal();

  expect(screen.getByText(EN.transformedLabel)).toBeInTheDocument();
  expect(chipLabels()).toEqual([EN.allQueriesChip, "Query 1", "Query 2"]);
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();

  expect(within(tree()).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree()).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree()).getByText("ParallelRetriever")).toBeInTheDocument();
  // BM25Retriever legitimately appears twice in the All view: once as the q1
  // parallel's child card and once as the q2 root card.
  expect(within(tree()).getAllByText("BM25Retriever")).toHaveLength(2);
  expect(within(tree()).getByText("TFIDFRetriever")).toBeInTheDocument();

  await userEvent.click(within(selector()).getByText("Query 2"));

  expect(
    within(tree()).queryByText("ParallelRetriever"),
  ).not.toBeInTheDocument();
  expect(within(tree()).queryByText("Query 1")).not.toBeInTheDocument();
  expect(within(tree()).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree()).getByText("BM25Retriever")).toBeInTheDocument();
  expect(screen.getByTestId("selected-query-text")).toHaveTextContent(
    "what is beta",
  );

  await userEvent.click(within(selector()).getByText(EN.allQueriesChip));

  expect(within(tree()).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree()).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree()).getByText("ParallelRetriever")).toBeInTheDocument();
  expect(within(tree()).getByText("TFIDFRetriever")).toBeInTheDocument();
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();
});

test("(g) clicking a surviving tree chunk highlights its card and keeps the static title", async () => {
  renderModal();

  await userEvent.click(within(selector()).getByText("Query 2"));
  await userEvent.click(screen.getByTestId("tree-chunk-2_1"));

  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 7")).toBeInTheDocument();
  expect(screen.getByTestId("trace-chunks-title")).toHaveTextContent(EN.title);
});

test("(h) clicking a right-panel chunk card sets the highlight", async () => {
  renderModal();

  await userEvent.click(screen.getByTestId("chunk-card-1_0"));

  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 3, page 2")).toBeInTheDocument();
});

test("(i) clicking a discarded chunk shows the snackbar and keeps the highlight", async () => {
  renderModal();

  await userEvent.click(screen.getAllByTestId("tree-chunk-9_9")[0]);

  expect(await screen.findByText(EN.discarded)).toBeInTheDocument();
  expect(
    screen.queryByTestId("highlighted-chunk-card"),
  ).not.toBeInTheDocument();
});

test("(j) entries with malformed retrievers are dropped from chips and trees", () => {
  renderModal({
    trace: [TRACE[0], { query: "bad", retriever: "not-an-object" }, TRACE[1]],
  });

  expect(chipLabels()).toEqual([EN.allQueriesChip, "Query 1", "Query 2"]);
  expect(within(tree()).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree()).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree()).queryByText("Query 3")).not.toBeInTheDocument();
});

test("(k) legacy trace=null keeps the bubble and the groups, without a tree", () => {
  renderModal({ trace: null });

  expect(screen.getByTestId("your-message-label")).toHaveTextContent(
    "Your message was:",
  );
  expect(
    within(screen.getByTestId("user-message-box")).getByText("What is alpha?"),
  ).toBeInTheDocument();
  expect(screen.queryByTestId("trace-tree")).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  expect(
    within(screen.getByTestId("doc-group-1")).getByText("Alpha.pdf"),
  ).toBeInTheDocument();
});

test("(l) a non-array trace renders only the info block without crashing", () => {
  renderModal({ trace: "oops" });

  expect(screen.getByTestId("your-message-label")).toHaveTextContent(
    "Your message was:",
  );
  expect(screen.queryByTestId("trace-tree")).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  expect(
    within(screen.getByTestId("doc-group-1")).getByText("Alpha.pdf"),
  ).toBeInTheDocument();
});

test("empty references show the empty state and make tree rows non-interactive", () => {
  renderModal({ references: null });

  const panel = screen.getByTestId("final-chunks-panel");
  expect(within(panel).getByText(EN.emptyState)).toBeInTheDocument();
  const rows = screen.getAllByTestId(/^tree-chunk-/);
  expect(rows.length).toBeGreaterThan(0);
  rows.forEach((row) => expect(row).not.toHaveAttribute("role", "button"));
});
