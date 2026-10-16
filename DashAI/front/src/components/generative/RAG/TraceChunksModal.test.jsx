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
  yourMessage: "Your message was",
  chunksTab: "Chunks",
  retrieverTab: "Retriever",
  selectedChunkHint: "Select a chunk from the tree to see its content here.",
  sectionsLabel: "Message source sections",
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

/**
 * Switches to the Retriever tab, whose panel hosts the story strip, the
 * selected-chunk panel/hint, the query selector and the retriever trees.
 * @returns {Promise<void>} Resolves once the click has been processed.
 */
async function openRetrieverTab() {
  await userEvent.click(screen.getByRole("tab", { name: EN.retrieverTab }));
}

beforeEach(() => {
  mockNavigate.mockClear();
});

test("(a) renders the translated static title", () => {
  renderModal();
  expect(screen.getByTestId("trace-chunks-title")).toHaveTextContent(EN.title);
});

test("(b) renders the user message once as a quiet quote under its label", () => {
  renderModal();

  expect(screen.getAllByText("What is alpha?")).toHaveLength(1);
  expect(screen.getByTestId("your-message-label")).toHaveTextContent(
    EN.yourMessage,
  );
  expect(screen.getByTestId("user-message-quote")).toHaveTextContent(
    "What is alpha?",
  );
});

test("(c) groups final chunks by document with a per-document count", () => {
  renderModal();

  const doc1 = screen.getByTestId("doc-group-1");
  expect(doc1).toBeVisible();
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

test("(e) story strip: rewritten when the query was transformed", async () => {
  renderModal();
  await openRetrieverTab();

  const panel = screen.getByTestId("retriever-tab-panel");
  const strip = within(panel).getByTestId("story-strip");
  expect(strip).toHaveTextContent(EN.storyRewritten2);
  expect(strip).toHaveTextContent(EN.storyKeptAll3);
});

test("(f) story strip: direct search when the query was not transformed", async () => {
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
  await openRetrieverTab();

  const panel = screen.getByTestId("retriever-tab-panel");
  expect(within(panel).getByTestId("story-strip")).toHaveTextContent(
    EN.storyDirect,
  );
});

test("(g) story strip: reports how many candidates survived", async () => {
  renderModal({
    trace: COUNT_TRACE,
    references: COUNT_REFERENCES,
  });
  await openRetrieverTab();

  const panel = screen.getByTestId("retriever-tab-panel");
  expect(within(panel).getByTestId("story-strip")).toHaveTextContent(
    EN.storyKept,
  );
});

test("(h) tabs default to Chunks and show the selector only when transformed", async () => {
  const { unmount } = renderModal();

  const chunksTab = screen.getByRole("tab", { name: EN.chunksTab });
  const retrieverTab = screen.getByRole("tab", { name: EN.retrieverTab });
  expect(chunksTab).toHaveAttribute("aria-selected", "true");
  expect(retrieverTab).toHaveAttribute("aria-selected", "false");
  expect(screen.getByTestId("chunks-tab-panel")).toBeVisible();
  expect(screen.getByTestId("retriever-tab-panel")).not.toBeVisible();

  await openRetrieverTab();
  expect(screen.getByTestId("retriever-tab-panel")).toBeVisible();
  expect(screen.getByTestId("chunks-tab-panel")).not.toBeVisible();
  expect(screen.getByTestId("trace-tree")).toBeInTheDocument();
  // The tablist announces itself with a section label of its own, not the
  // dialog title it would otherwise duplicate.
  expect(screen.getByRole("tablist")).toHaveAttribute(
    "aria-label",
    EN.sectionsLabel,
  );
  // The transformed fixture (two queries) exposes the selector.
  expect(screen.getByTestId("query-selector")).toBeInTheDocument();
  // Nothing is selected yet, so the quiet hint stands in for the chunk panel.
  expect(screen.getByTestId("selected-chunk-hint")).toBeVisible();
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
  await openRetrieverTab();
  expect(screen.getByTestId("trace-tree")).toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  // The hint is independent of the query transformation: it only requires an
  // intact reference map.
  expect(screen.getByTestId("selected-chunk-hint")).toBeInTheDocument();
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
  await openRetrieverTab();

  expect(screen.getByText(EN.discardedTitle)).toBeInTheDocument();
  const chip = screen.getByTestId("discarded-chip-9_9");
  expect(chip).toHaveTextContent("9_9");

  await userEvent.click(chip);
  expect(await screen.findByText(EN.discarded)).toBeInTheDocument();
});

test("(m) selector defaults to all trees and filters to one query", async () => {
  renderModal();
  await openRetrieverTab();

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

test("(n) clicking a surviving tree chunk selects it and highlights its card", async () => {
  renderModal();
  await openRetrieverTab();

  await userEvent.click(within(selector()).getByText("Query 2"));
  await userEvent.click(screen.getByTestId("tree-chunk-2_1"));

  const panel = screen.getByTestId("selected-chunk-panel");
  expect(within(panel).getByText("Chunk 7")).toBeInTheDocument();
  expect(within(panel).getByText("beta text")).toBeInTheDocument();
  // A resolvable selection replaces the hint.
  expect(screen.queryByTestId("selected-chunk-hint")).not.toBeInTheDocument();

  // The hidden Chunks tab still surfaces the matching highlighted card.
  await userEvent.click(screen.getByRole("tab", { name: EN.chunksTab }));
  expect(screen.getByTestId("chunks-tab-panel")).toBeVisible();
  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 7")).toBeInTheDocument();
});

test("(o) clicking a chunk card highlights it and selects it in the retriever tab", async () => {
  renderModal();

  await userEvent.click(screen.getByTestId("chunk-card-1_0"));

  const card = screen.getByTestId("highlighted-chunk-card");
  expect(within(card).getByText("Chunk 3, page 2")).toBeInTheDocument();

  await openRetrieverTab();
  const panel = screen.getByTestId("selected-chunk-panel");
  expect(within(panel).getByText("Chunk 3, page 2")).toBeInTheDocument();
  expect(within(panel).getByText("alpha text")).toBeInTheDocument();
  expect(screen.queryByTestId("selected-chunk-hint")).not.toBeInTheDocument();
});

test("(p) clicking a discarded tree chunk warns without selecting", async () => {
  renderModal();
  await openRetrieverTab();

  await userEvent.click(screen.getAllByTestId("tree-chunk-9_9")[0]);

  expect(await screen.findByText(EN.discarded)).toBeInTheDocument();
  expect(screen.queryByTestId("selected-chunk-panel")).not.toBeInTheDocument();
});

test("(q) drops malformed trace entries from the selector and trees", async () => {
  renderModal({
    trace: [TRACE[0], { query: "bad", retriever: "not-an-object" }, TRACE[1]],
  });
  await openRetrieverTab();

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

test("(r) legacy trace=null keeps the quote and groups, without tabs", () => {
  renderModal({ trace: null });

  expect(screen.getByTestId("user-message-quote")).toHaveTextContent(
    "What is alpha?",
  );
  expect(screen.queryByTestId("trace-tabs")).not.toBeInTheDocument();
  expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  // The "your message" caption is intentionally tabbed-branch only.
  expect(screen.queryByTestId("your-message-label")).not.toBeInTheDocument();
  expect(screen.queryByTestId("story-strip")).not.toBeInTheDocument();
  expect(screen.queryByTestId("trace-tree")).not.toBeInTheDocument();
  expect(screen.queryByTestId("query-selector")).not.toBeInTheDocument();
  expect(
    within(screen.getByTestId("doc-group-1")).getByText("Alpha.pdf"),
  ).toBeInTheDocument();
});

test("(s) a non-array trace renders without crashing and without tabs", () => {
  renderModal({ trace: "oops" });

  expect(screen.getByTestId("user-message-quote")).toBeInTheDocument();
  expect(screen.queryByTestId("trace-tabs")).not.toBeInTheDocument();
  expect(screen.queryByRole("tab")).not.toBeInTheDocument();
  // The "your message" caption is intentionally tabbed-branch only.
  expect(screen.queryByTestId("your-message-label")).not.toBeInTheDocument();
  expect(screen.getByTestId("doc-group-1")).toBeInTheDocument();
});

test("(t) empty references show the empty state and make tree rows non-interactive", async () => {
  renderModal({ references: null });

  // The Chunks tab is the default, so the empty state is what the user sees.
  expect(screen.getByText(EN.emptyState)).toBeInTheDocument();

  await openRetrieverTab();
  const rows = screen.getAllByTestId(/^tree-chunk-/);
  expect(rows.length).toBeGreaterThan(0);
  rows.forEach((row) => expect(row).not.toHaveAttribute("role", "button"));
  // With no reference map the rows are inert, so the hint's invitation to
  // select a chunk would be an impossible action — it must not render.
  expect(screen.queryByTestId("selected-chunk-hint")).not.toBeInTheDocument();
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

test("(w) cross-encoder scores render inline on their tree rows", async () => {
  renderModal({
    userMessage: "what is alpha",
    trace: SCORE_TRACE,
    references: { "1_0": DOC_1_0 },
  });
  await openRetrieverTab();

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

test("(x) discarded chips: hidden without a reference map, all candidates with an empty one", async () => {
  const { unmount } = renderModal({ references: null });
  await openRetrieverTab();
  expect(screen.queryByTestId("discarded-chip-9_9")).not.toBeInTheDocument();
  unmount();

  renderModal({ references: {} });
  await openRetrieverTab();
  expect(screen.getByTestId("discarded-chip-1_0")).toBeInTheDocument();
  expect(screen.getByTestId("discarded-chip-9_9")).toBeInTheDocument();
  expect(screen.getByTestId("discarded-chip-2_1")).toBeInTheDocument();
  // An empty map also leaves the rows inert, so the hint is hidden here too.
  expect(screen.queryByTestId("selected-chunk-hint")).not.toBeInTheDocument();
});

test("(y) a trace that shrinks while open falls back to the All view", async () => {
  const first = renderModal();
  await openRetrieverTab();
  await userEvent.click(within(selector()).getByText("Query 2"));

  first.rerenderWith({ trace: [TRACE[0]] });

  const tree = screen.getByTestId("trace-tree");
  expect(within(tree).getByText("Query 1")).toBeInTheDocument();
  expect(within(tree).getByText("ParallelRetriever")).toBeInTheDocument();
  expect(screen.queryByTestId("selected-query-text")).not.toBeInTheDocument();
});

test("(z) switching tabs preserves the retriever query selection", async () => {
  renderModal();
  await openRetrieverTab();
  await userEvent.click(within(selector()).getByText("Query 2"));
  expect(screen.getByTestId("selected-query-text")).toHaveTextContent(
    "what is beta",
  );

  await userEvent.click(screen.getByRole("tab", { name: EN.chunksTab }));
  await openRetrieverTab();

  expect(screen.getByTestId("selected-query-text")).toHaveTextContent(
    "what is beta",
  );
  expect(screen.queryByText("ParallelRetriever")).not.toBeInTheDocument();
});

test("(aa) reopening the modal resets the active tab to Chunks", async () => {
  const first = renderModal();
  await openRetrieverTab();
  expect(screen.getByRole("tab", { name: EN.retrieverTab })).toHaveAttribute(
    "aria-selected",
    "true",
  );

  first.rerenderWith({ open: false });
  first.rerenderWith({ open: true });

  expect(screen.getByRole("tab", { name: EN.chunksTab })).toHaveAttribute(
    "aria-selected",
    "true",
  );
  expect(screen.getByRole("tab", { name: EN.retrieverTab })).toHaveAttribute(
    "aria-selected",
    "false",
  );
});

test("(bb) a polling identity change does not reset tab or selection mid-read", async () => {
  const first = renderModal();
  await openRetrieverTab();
  await userEvent.click(within(selector()).getByText("Query 2"));
  await userEvent.click(screen.getByTestId("tree-chunk-2_1"));

  let panel = screen.getByTestId("selected-chunk-panel");
  expect(within(panel).getByText("Chunk 7")).toBeInTheDocument();

  // The chat polls and rebuilds references with a NEW identity, same content.
  first.rerenderWith({ references: { ...REFERENCES } });

  const retrieverPanel = screen.getByTestId("retriever-tab-panel");
  panel = within(retrieverPanel).getByTestId("selected-chunk-panel");
  expect(within(panel).getByText("Chunk 7")).toBeInTheDocument();
  expect(within(panel).getByText("beta text")).toBeInTheDocument();
  expect(screen.getByRole("tab", { name: EN.retrieverTab })).toHaveAttribute(
    "aria-selected",
    "true",
  );

  await userEvent.click(screen.getByRole("tab", { name: EN.chunksTab }));
  expect(screen.getByTestId("chunks-tab-panel")).toBeVisible();
  expect(screen.getByTestId("highlighted-chunk-card")).toBeInTheDocument();
});

describe("(cc) tab-aware scroll effect", () => {
  let scrollIntoView;

  beforeAll(() => {
    // jsdom implements neither scrollIntoView nor matchMedia; stub the former
    // so the effect's guard (`typeof el.scrollIntoView === "function"`) passes
    // and the reduce-motion branch resolves to the default "smooth" behaviour.
    scrollIntoView = jest.fn();
    Element.prototype.scrollIntoView = scrollIntoView;
  });

  afterAll(() => {
    delete Element.prototype.scrollIntoView;
  });

  beforeEach(() => {
    scrollIntoView.mockClear();
  });

  test("scrolls the highlighted card on Chunks, then the selected panel on Retriever", async () => {
    renderModal();

    await userEvent.click(screen.getByTestId("chunk-card-1_0"));
    const card = screen.getByTestId("highlighted-chunk-card");
    expect(card.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "nearest",
    });

    scrollIntoView.mockClear();

    await openRetrieverTab();
    await userEvent.click(within(selector()).getByText("Query 2"));
    await userEvent.click(screen.getByTestId("tree-chunk-2_1"));

    const selectedPanel = screen.getByTestId("selected-chunk-panel");
    expect(selectedPanel.scrollIntoView).toHaveBeenCalledWith({
      behavior: "smooth",
      block: "nearest",
    });
  });
});
