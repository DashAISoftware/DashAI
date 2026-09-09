import React from "react";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import RAGConfigPanel from "./RAGConfigPanel";

// One stable object: the panel's loader depends on `enqueueSnackbar`, so a
// fresh reference per render would restart the load on every render.
jest.mock("notistack", () => {
  const snackbar = { enqueueSnackbar: jest.fn() };
  return { useSnackbar: () => snackbar };
});

jest.mock("../../../api/rag", () => ({
  getChunkingPresets: jest.fn(),
  getRAGSession: jest.fn(),
  getRetrieverComponents: jest.fn(),
  getRetrieverPresets: jest.fn(),
  getSessionConfiguration: jest.fn(),
  updateGenerativeSessionParams: jest.fn(),
  getDefaultPrompts: jest.fn(),
}));
jest.mock("../../../api/session", () => ({
  updateGenerativeSession: jest.fn(),
}));
jest.mock("../../../pages/generative/RAGSession/retrieverKinds", () => ({
  loadRetrieverKinds: jest.fn(),
}));
// The generator picker fetches components and download state of its own; the
// panel only cares about the availability it reports back.
jest.mock("./GeneratorPicker", () => {
  const MockGeneratorPicker = () => <div data-testid="generator-picker" />;
  return MockGeneratorPicker;
});
jest.mock(
  "../../../pages/generative/RAGSession/advanced/ChunkingAdvancedModal",
  () => {
    const MockChunkingAdvancedModal = () => null;
    return MockChunkingAdvancedModal;
  },
);
jest.mock(
  "../../../pages/generative/RAGSession/advanced/RetrieverAdvancedModal",
  () => {
    const MockRetrieverAdvancedModal = () => null;
    return MockRetrieverAdvancedModal;
  },
);

const api = require("../../../api/rag");
const {
  loadRetrieverKinds,
} = require("../../../pages/generative/RAGSession/retrieverKinds");

const CHUNKING_PRESETS = [
  {
    key: "balanced",
    display_name: "Balanced",
    description: "A middling chunk size",
    component: "CharacterChunkModel",
    params: { chunk_size: 400, chunk_overlap: 40 },
  },
  {
    key: "fine",
    display_name: "Fine",
    description: "Smaller chunks",
    component: "CharacterChunkModel",
    params: { chunk_size: 200, chunk_overlap: 20 },
  },
];

const RETRIEVER_PRESETS = [
  {
    key: "keyword",
    display_name: "Keyword",
    description: "BM25",
    component: "BM25Retriever",
    params: { top_k: 5 },
  },
];

const SESSION = {
  id: 1,
  name: "A session",
  description: "",
  parameters: {
    documents: [],
    chunking_model: CHUNKING_PRESETS[0],
    retriever_model: RETRIEVER_PRESETS[0],
    prompt: {
      component: "CustomRAGGenerationPrompt",
      params: { template: "Use {chunks} for {input}", language: "en" },
    },
    generation_model: { component: "StubLLM", params: {} },
  },
};

/** The shape `getSessionConfiguration` returns, with backend-localized names. */
const CONFIGURATION = {
  chunking_model: {
    section_name: "Chunking",
    component: "CharacterChunkModel",
    display_name: "Character",
    description: "How documents are split",
    registered: true,
    params: [],
    preset_key: "balanced",
    preset_display_name: "Balanced",
    summary: "400 characters",
  },
  retriever_model: {
    section_name: "Retrieval",
    component: "BM25Retriever",
    display_name: "BM25",
    description: "How passages are found",
    registered: true,
    params: [],
    preset_key: "keyword",
    preset_display_name: "Keyword",
    top_k: 5,
  },
  generation_model: {
    section_name: "Model",
    component: "StubLLM",
    display_name: "Stub",
    description: "Which model answers",
    registered: true,
    params: [],
  },
  prompt: {
    section_name: "Prompt",
    component: "CustomRAGGenerationPrompt",
    display_name: "Custom",
    description: "How the question is phrased",
    registered: true,
    params: [],
  },
  context_budget: {
    context_window: 4096,
    available: 3000,
    is_valid: true,
  },
};

beforeEach(() => {
  jest.clearAllMocks();
  api.getRAGSession.mockResolvedValue(SESSION);
  api.getSessionConfiguration.mockResolvedValue(CONFIGURATION);
  api.getChunkingPresets.mockResolvedValue(CHUNKING_PRESETS);
  api.getRetrieverPresets.mockResolvedValue(RETRIEVER_PRESETS);
  api.getRetrieverComponents.mockResolvedValue([]);
  api.updateGenerativeSessionParams.mockResolvedValue({});
  api.getDefaultPrompts.mockResolvedValue([]);
  loadRetrieverKinds.mockResolvedValue({});
});

/** Renders the panel and waits for its initial load. */
async function renderPanel(props = {}) {
  const onSaved = jest.fn();
  const onRetryIndexing = jest.fn();
  renderWithProviders(
    <RAGConfigPanel
      sessionId={1}
      onSaved={onSaved}
      onRetryIndexing={onRetryIndexing}
      {...props}
    />,
  );
  await screen.findByRole("tab", { name: /Chunking/ });
  return { onSaved, onRetryIndexing };
}

test("renders one tab per section, labelled by the backend", async () => {
  await renderPanel();
  for (const label of ["Chunking", "Retrieval", "Model", "Prompt"]) {
    expect(
      screen.getByRole("tab", { name: new RegExp(label) }),
    ).toBeInTheDocument();
  }
});

test("saving is offered only once something changed", async () => {
  await renderPanel();
  const save = screen.getByRole("button", { name: /Save/i });
  expect(save).toBeDisabled();

  await userEvent.click(screen.getByText("Fine"));
  await waitFor(() => expect(save).toBeEnabled());
});

test("an edit on a hidden tab is still reported and still saved", async () => {
  await renderPanel();

  // Change chunking, then move to a different tab: the change is now off
  // screen, which is exactly when the panel has to keep saying it exists.
  await userEvent.click(screen.getByText("Fine"));
  await userEvent.click(screen.getByRole("tab", { name: /Model/ }));

  const chunkingTab = screen.getByRole("tab", { name: /Chunking/ });
  expect(
    within(chunkingTab).getByTestId("FiberManualRecordIcon"),
  ).toBeInTheDocument();

  const save = screen.getByRole("button", { name: /Save/i });
  await waitFor(() => expect(save).toBeEnabled());
  await userEvent.click(save);

  // One request carries the whole draft: the endpoint replaces every
  // parameter at once, so a per-tab save would be a lie.
  await waitFor(() =>
    expect(api.updateGenerativeSessionParams).toHaveBeenCalledTimes(1),
  );
  const [, sent] = api.updateGenerativeSessionParams.mock.calls[0];
  expect(sent.chunking_model.params.chunk_size).toBe(200);
  expect(sent.retriever_model).toEqual(RETRIEVER_PRESETS[0]);
  expect(sent.prompt.params.template).toBe("Use {chunks} for {input}");
});

test("discarding puts every tab back to the saved configuration", async () => {
  await renderPanel();

  await userEvent.click(screen.getByText("Fine"));
  const discard = screen.getByRole("button", { name: /Discard/i });
  await waitFor(() => expect(discard).toBeEnabled());

  await userEvent.click(discard);

  await waitFor(() =>
    expect(screen.getByRole("button", { name: /Save/i })).toBeDisabled(),
  );
  expect(api.updateGenerativeSessionParams).not.toHaveBeenCalled();
});

test("the four sections sit two by two rather than in one scrolling row", async () => {
  await renderPanel();

  // The panel can be squeezed to 15% of the window and the labels come from the
  // backend -- Spanish "Fragmentación"/"Recuperación" is the worst case at 37
  // characters across four tabs. Four abreast either wrap or hide half of
  // themselves behind a scroll button; two rows of two keep all four legible.
  const tablist = screen.getByRole("tablist");
  const style = getComputedStyle(tablist);
  expect(style.display).toBe("grid");
  expect(style.gridTemplateColumns).toBe("repeat(2, 1fr)");

  expect(screen.getAllByRole("tab")).toHaveLength(4);
  // Not the scrollable variant: nothing is parked off screen.
  expect(tablist.parentElement.className).not.toMatch(/scrollableX/);
});

test("every section is mounted, so a tab never opened still validates", async () => {
  await renderPanel();
  // The generator reports whether its model can run through a callback. If it
  // only mounted once its tab was opened, Save would stay enabled for a model
  // that cannot answer.
  expect(screen.getByTestId("generator-picker")).toBeInTheDocument();
});

// ─── Indexing notices ──────────────────────────────────────────────────
// Indexing now runs up front rather than on the first message, so the panel
// is where its progress and its failures surface.

test("a running index shows its progress, using the backend's wording", async () => {
  await renderPanel({
    indexStatus: {
      status: "indexing",
      message: "Indexing the documents…",
      job: { status: "started", progress: 40 },
    },
  });

  // Scoped to the notice: the panel also draws a context-budget bar, and a
  // bare progressbar query would not tell the two apart.
  const notice = screen.getByRole("alert");
  expect(
    within(notice).getByText("Indexing the documents…"),
  ).toBeInTheDocument();
  expect(within(notice).getByRole("progressbar")).toHaveAttribute(
    "aria-valuenow",
    "40",
  );
});

test("an index with no progress yet shows an indeterminate bar", async () => {
  // A determinate bar sitting at 0% reads as stalled rather than as starting.
  await renderPanel({
    indexStatus: {
      status: "indexing",
      message: "Indexing the documents…",
      job: { status: "not_started", progress: null },
    },
  });

  const notice = screen.getByRole("alert");
  expect(within(notice).getByRole("progressbar")).not.toHaveAttribute(
    "aria-valuenow",
  );
});

test("a stale index warns without claiming to be working", async () => {
  await renderPanel({
    indexStatus: {
      status: "stale",
      message: "The configuration changed.",
      job: null,
    },
  });

  const notice = screen.getByRole("alert");
  expect(
    within(notice).getByText("The configuration changed."),
  ).toBeInTheDocument();
  expect(within(notice).queryByRole("progressbar")).not.toBeInTheDocument();
});

test("a failed index stays visible and offers a retry", async () => {
  const { onRetryIndexing } = await renderPanel({
    indexStatus: {
      status: "not_indexed",
      message: "These documents are not indexed yet.",
      job: { status: "error", error: "Out of memory" },
    },
  });

  const notice = screen.getByRole("alert");
  expect(within(notice).getByText("Out of memory")).toBeInTheDocument();
  await userEvent.click(within(notice).getByRole("button", { name: /Retry/i }));
  expect(onRetryIndexing).toHaveBeenCalledTimes(1);
});

test("a job that finished cleanly raises no alarm", async () => {
  await renderPanel({
    indexStatus: {
      status: "indexed",
      message: "The documents are indexed.",
      job: { status: "finished", progress: 100, error: null },
    },
  });

  expect(screen.queryByRole("alert")).not.toBeInTheDocument();
});
