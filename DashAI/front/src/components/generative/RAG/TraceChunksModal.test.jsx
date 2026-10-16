import React from "react";
import { screen, within, fireEvent } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { SnackbarProvider } from "notistack";
import { render } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { I18nextProvider } from "react-i18next";
import { ThemeProvider, createTheme } from "@mui/material/styles";
import getTheme from "../../../styles/theme";
import i18n from "../../../utils/i18n";
import { ColorModeContext } from "../../../contexts/ThemeContext";
import TraceChunksModal from "./TraceChunksModal";

// Mirrors renderWithProviders' tree so rerenders can keep the SAME provider
// structure: RTL's rerender replaces the whole rendered element, and any
// provider-shape mismatch would remount the modal and reset its state,
// masking polling-related regressions.
function Providers({ children }) {
  const theme = createTheme(getTheme("dark"));
  return (
    <ColorModeContext.Provider value={{ toggleColorMode: jest.fn() }}>
      <ThemeProvider theme={theme}>
        <I18nextProvider i18n={i18n}>
          <MemoryRouter>
            <SnackbarProvider>{children}</SnackbarProvider>
          </MemoryRouter>
        </I18nextProvider>
      </ThemeProvider>
    </ColorModeContext.Provider>
  );
}

const mockNavigate = jest.fn();
jest.mock("react-router-dom", () => {
  const actual = jest.requireActual("react-router-dom");
  return { ...actual, useNavigate: () => mockNavigate };
});

// Exact English strings the real locale bundle must expose under
// `generative.traceChunks`; the suite relies on the shipped translations.
const EN = {
  title: "Message sources",
  receivedTitle: "Chunks used for this answer",
  methodTitle: "How these chunks were selected",
  storyDirect: "The retriever searched with your message directly.",
  storyRewritten2: "Your message was rewritten into 2 search queries.",
  storyKeptAll3: "All 3 retrieved chunks reached the answer.",
  storyKept: "3 of 4 retrieved chunks reached the answer.",
  foundBy: "Found by BM25Retriever (query 1)",
  discarded:
    "This chunk was discarded: it did not reach the end of the pipeline.",
  discardedTitle: "Discarded during selection",
  emptyState: "No chunks were retrieved for this response.",
  openDocument: "Open document",
  close: "Close",
  showMore: "Show more",
  showLess: "Show less",
};

const DOC_1_0 = {
  document_id: 1,
  document_name: "Alpha.pdf",
  document_position: 3,
  page: 2,
  text: "alpha text",
};
const DOC_2_1 = {
  document_id: 2,
  document_name: "Beta.pdf",
  document_position: 7,
  page: null,
  text: "beta text",
};
const DOC_1_3 = {
  document_id: 1,
  document_name: "Alpha.pdf",
  document_position: 5,
  page: 4,
  text: "gamma text",
};

const REFERENCES = { "1_0": DOC_1_0, "2_1": DOC_2_1, "1_3": DOC_1_3 };

// Two queries (transformed), a composite first retriever whose ref "9_9" is
// dropped downstream, and a plain leaf second query.
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

// A ref present in both the composite root and its BM25 child; the deepest
// node wins, so provenance is "BM25Retriever (query 1)".
const PROV_TRACE = [
  {
    query: "rewritten query",
    retriever: {
      name: "ParallelRetriever",
      chunks: ["1_0", "9_9"],
      children: [
        { name: "BM25Retriever", chunks: ["1_0"] },
        { name: "TFIDFRetriever", chunks: ["9_9"] },
      ],
    },
  },
];
const PROV_REFERENCES = { "1_0": DOC_1_0 };

// Four distinct candidates across two queries, three of which survive.
const COUNT_TRACE = [
  {
    query: "q one",
    retriever: { name: "BM25Retriever", chunks: ["1_0", "2_1", "4_4"] },
  },
  { query: "q two", retriever: { name: "TFIDFRetriever", chunks: ["3_3"] } },
];
const COUNT_REFERENCES = {
  "1_0": DOC_1_0,
  "2_1": DOC_2_1,
  "3_3": {
    document_id: 3,
    document_name: "Gamma.pdf",
    document_position: 1,
    page: null,
    text: "gamma",
  },
};

const LONG_TEXT = "lorem ipsum ".repeat(60);
const LONG_TRACE = [
  {
    query: "what is alpha",
    retriever: { name: "BM25Retriever", chunks: ["1_0"] },
  },
];
const LONG_REFERENCES = { "1_0": { ...DOC_1_0, text: LONG_TEXT } };

function renderModal(overrides = {}) {
  const onClose = jest.fn();
  const props = {
    open: true,
    onClose,
    userMessage: "What is alpha?",
    trace: TRACE,
    references: REFERENCES,
    ...overrides,
  };
  const ui = (nextProps) => (
    <Providers>
      <TraceChunksModal {...nextProps} />
    </Providers>
  );
  const result = render(ui(props));
  return {
    ...result,
    onClose,
    // Re-renders with new props while PRESERVING the provider tree, so the
    // component updates in place instead of remounting (a remount would reset
    // its state and mask polling-related regressions).
    rerenderWith: (newOverrides) =>
      result.rerender(ui({ ...props, ...newOverrides })),
  };
}

function selector() {
  return screen.getByTestId("query-selector");
}

beforeEach(() => {
  mockNavigate.mockClear();
});

test("(a) renders the translated static title", () => {
  renderModal();
  expect(screen.getByTestId("trace-chunks-title")).toHaveTextContent(EN.title);
});

test("(b) renders the user message once as a quiet quote", () => {
  renderModal();

  expect(screen.getAllByText("What is alpha?")).toHaveLength(1);
  expect(screen.getByTestId("user-message-quote")).toHaveTextContent(
    "What is alpha?",
  );
});

test("(c) groups final chunks by document with a per-document count", () => {
  renderModal();

  const doc1 = screen.getByTestId("doc-group-1");
  expect(within(doc1).getByText("Alpha.pdf")).toBeInTheDocument();
  expect(within(doc1).getByText("2 chunks")).toBeInTheDocument();

  const doc2 = screen.getByTestId("doc-group-2");
  expect(within(doc2).getByText("Beta.pdf")).toBeInTheDocument();
  expect(within(doc2).getByText("1 chunk")).toBeInTheDocument();
});

test("(d) shows the received heading with a chunk/document count", () => {
  renderModal();

  expect(screen.getByTestId("received-title")).toHaveTextContent(
    EN.receivedTitle,
  );
  expect(screen.getByTestId("received-count")).toHaveTextContent(
    "3 chunks from 2 documents",
  );
});

test("(e) story strip: rewritten when the query was transformed", () => {
  renderModal();

  const strip = screen.getByTestId("story-strip");
  expect(strip).toHaveTextContent(EN.storyRewritten2);
  expect(strip).toHaveTextContent(EN.storyKeptAll3);
});

test("(f) story strip: direct search when the query was not transformed", () => {
  renderModal({
    userMessage: "what is alpha",
    trace: [
      {
        query: "what is alpha",
        retriever: { name: "BM25Retriever", chunks: ["1_0"] },
      },
    ],
    references: { "1_0": DOC_1_0 },
  });

  expect(screen.getByTestId("story-strip")).toHaveTextContent(EN.storyDirect);
});

test("(g) story strip: reports how many candidates survived", () => {
  renderModal({
    trace: COUNT_TRACE,
    references: COUNT_REFERENCES,
  });

  expect(screen.getByTestId("story-strip")).toHaveTextContent(EN.storyKept);
});

test("(h) method panel is expanded for a transformed query and collapsed otherwise", () => {
  const { unmount } = renderModal();
  expect(
    within(screen.getByTestId("method-panel")).getByRole("button", {
      name: EN.methodTitle,
    }),
  ).toHaveAttribute("aria-expanded", "true");
  unmount();

  renderModal({
    userMessage: "what is alpha",
    trace: [
      {
        query: "what is alpha",
        retriever: { name: "BM25Retriever", chunks: ["1_0"] },
      },
    ],
    references: { "1_0": DOC_1_0 },
  });
  expect(
    within(screen.getByTestId("method-panel")).getByRole("button", {
      name: EN.methodTitle,
    }),
  ).toHaveAttribute("aria-expanded", "false");
});

test("(i) has no DialogActions footer, only a per-document Open document icon", () => {
  renderModal();

  expect(screen.getAllByRole("button", { name: EN.openDocument })).toHaveLength(
    2,
  );
  // The old footer rendered a plain-text Close button; the new close control is
  // an icon button with an accessible name but no visible text.
  expect(screen.queryByText(EN.close)).not.toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: EN.close })).toHaveLength(1);
});

test("(j) Open document navigates to the document route and closes the modal", async () => {
  const { onClose } = renderModal();

  await userEvent.click(
    screen.getAllByRole("button", { name: EN.openDocument })[0],
  );

  expect(mockNavigate).toHaveBeenCalledWith("/app/data/documents/1");
  expect(onClose).toHaveBeenCalled();
});

test("(k) attributes a surviving chunk to its deepest retriever and query", () => {
  renderModal({ trace: PROV_TRACE, references: PROV_REFERENCES });

  expect(screen.getByText(EN.foundBy)).toBeInTheDocument();
});

test("(l) renders discarded candidates as chips and warns when clicked", async () => {
  renderModal();

  expect(screen.getByText(EN.discardedTitle)).toBeInTheDocument();
  const chip = screen.getByTestId("discarded-chip-9_9");
  expect(chip).toHaveTextContent("9_9");

  await userEvent.click(chip);
  expect(await screen.findByText(EN.discarded)).toBeInTheDocument();
});

test("(m) selector defaults to all trees and filters to one query", async () => {
  renderModal();

  expect(
    within(selector())
      .getAllByTestId("query-chip")
      .map((chip) => chip.textContent),
  ).toEqual(["All", "Query 1", "Query 2"]);
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();

  const tree = screen.getByTestId("trace-tree");
  expect(within(tree).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree).getByText("ParallelRetriever")).toBeInTheDocument();
  // BM25Retriever appears twice in the All view: the q1 child and the q2 root.
  expect(within(tree).getAllByText("BM25Retriever")).toHaveLength(2);

  await userEvent.click(within(selector()).getByText("Query 2"));

  expect(screen.queryByText("ParallelRetriever")).not.toBeInTheDocument();
  expect(screen.getByTestId("selected-query-text")).toHaveTextContent(
    "what is beta",
  );
});

test("(n) clicking a surviving tree chunk highlights its card", async () => {
  renderModal();

  await userEvent.click(within(selector()).getByText("Query 2"));
  await userEvent.click(screen.getByTestId("tree-chunk-2_1"));

  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 7")).toBeInTheDocument();
});

test("(o) clicking a chunk card highlights it", async () => {
  renderModal();

  await userEvent.click(screen.getByTestId("chunk-card-1_0"));

  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 3, page 2")).toBeInTheDocument();
});

test("(p) clicking a discarded tree chunk warns without highlighting", async () => {
  renderModal();

  await userEvent.click(screen.getAllByTestId("tree-chunk-9_9")[0]);

  expect(await screen.findByText(EN.discarded)).toBeInTheDocument();
  expect(
    screen.queryByTestId("highlighted-chunk-card"),
  ).not.toBeInTheDocument();
});

test("(q) drops malformed trace entries from the selector and trees", () => {
  renderModal({
    trace: [TRACE[0], { query: "bad", retriever: "not-an-object" }, TRACE[1]],
  });

  expect(
    within(selector())
      .getAllByTestId("query-chip")
      .map((chip) => chip.textContent),
  ).toEqual(["All", "Query 1", "Query 2"]);
  const tree = screen.getByTestId("trace-tree");
  expect(within(tree).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree).getByText("Query 2")).toBeInTheDocument();
  expect(within(tree).queryByText("Query 3")).not.toBeInTheDocument();
});

test("(r) legacy trace=null keeps the quote and groups, without a method panel", () => {
  renderModal({ trace: null });

  expect(screen.getByTestId("user-message-quote")).toHaveTextContent(
    "What is alpha?",
  );
  expect(screen.queryByTestId("story-strip")).not.toBeInTheDocument();
  expect(screen.queryByTestId("method-panel")).not.toBeInTheDocument();
  expect(screen.queryByTestId("trace-tree")).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  expect(
    within(screen.getByTestId("doc-group-1")).getByText("Alpha.pdf"),
  ).toBeInTheDocument();
});

test("(s) a non-array trace renders without crashing", () => {
  renderModal({ trace: "oops" });

  expect(screen.getByTestId("user-message-quote")).toBeInTheDocument();
  expect(screen.queryByTestId("method-panel")).not.toBeInTheDocument();
  expect(screen.getByTestId("doc-group-1")).toBeInTheDocument();
});

test("(t) empty references show the empty state and make tree rows non-interactive", () => {
  renderModal({ references: null });

  expect(screen.getByText(EN.emptyState)).toBeInTheDocument();
  expect(screen.getByTestId("method-panel")).toBeInTheDocument();

  const rows = screen.getAllByTestId(/^tree-chunk-/);
  expect(rows.length).toBeGreaterThan(0);
  rows.forEach((row) => expect(row).not.toHaveAttribute("role", "button"));
});

test("(u) long chunk text collapses behind Show more and expands again", async () => {
  renderModal({
    userMessage: "what is alpha",
    trace: LONG_TRACE,
    references: LONG_REFERENCES,
  });

  await userEvent.click(screen.getByRole("button", { name: EN.showMore }));
  expect(screen.getByRole("button", { name: EN.showLess })).toBeInTheDocument();
});

test("(v) chunk cards are keyboard operable", () => {
  renderModal();

  const card = screen.getByTestId("chunk-card-1_0");
  fireEvent.keyDown(card, { key: "Enter" });

  expect(screen.getByTestId("highlighted-chunk-card")).toBeInTheDocument();
});

const SCORE_TRACE = [
  {
    query: "what is alpha",
    retriever: {
      name: "CrossEncoderRetriever",
      chunks: ["1_0"],
      scores: [
        { ref: "1_0", score: 0.98712 },
        { ref: "9_9", score: 0.12345 },
      ],
      children: [{ name: "BM25Retriever", chunks: ["1_0", "9_9"] }],
    },
  },
];

test("(w) cross-encoder scores render inline on their tree rows", () => {
  renderModal({
    userMessage: "what is alpha",
    trace: SCORE_TRACE,
    references: { "1_0": DOC_1_0 },
  });

  // The ref renders at both the reranker root (which owns the scores) and its
  // BM25 child; only the root's row carries the inline score.
  const scored = screen
    .getAllByTestId("tree-chunk-1_0")
    .some((row) => /0\.987/.test(row.textContent));
  expect(scored).toBe(true);
  // A score for a candidate that is not rendered at this node stays hidden.
  expect(screen.queryByText("0.123")).not.toBeInTheDocument();
  expect(screen.queryByText("Scores")).not.toBeInTheDocument();
});

test("(x) discarded chips: hidden without a reference map, all candidates with an empty one", () => {
  const { unmount } = renderModal({ references: null });
  expect(screen.queryByTestId("discarded-chip-9_9")).not.toBeInTheDocument();
  unmount();

  renderModal({ references: {} });
  expect(screen.getByTestId("discarded-chip-1_0")).toBeInTheDocument();
  expect(screen.getByTestId("discarded-chip-9_9")).toBeInTheDocument();
  expect(screen.getByTestId("discarded-chip-2_1")).toBeInTheDocument();
});

test("(y) a trace that shrinks while open falls back to the All view", async () => {
  const first = renderModal();
  await userEvent.click(within(selector()).getByText("Query 2"));

  first.rerenderWith({ trace: [TRACE[0]] });

  const tree = screen.getByTestId("trace-tree");
  expect(within(tree).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree).getByText("ParallelRetriever")).toBeInTheDocument();
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();
});
