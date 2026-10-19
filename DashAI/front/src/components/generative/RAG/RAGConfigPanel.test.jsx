import React from "react";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import RAGConfigPanel from "./RAGConfigPanel";

// The unmocked QueryTransformationPicker pulls the shared form machinery in,
// and form cards describe fields through react-markdown, which ships ESM only
// and CRA's jest does not transform node_modules. See
// FormSchemaRenderFields.test.jsx for the same workaround.
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

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
  getGeneratorComponents: jest.fn(),
  getQueryTransformationComponents: jest.fn(),
  getQueryTransformationPrompts: jest.fn(),
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

const TRANSFORMERS = [
  {
    name: "LLMQueryRewriter",
    display_name: "Rewriter",
    description: "One self-contained query",
    metadata: { technique: "rewriting", prompt_parent: "QueryRewritingPrompt" },
  },
  {
    name: "LLMQueryExpander",
    display_name: "Expander",
    description: "Several broader queries",
    metadata: { technique: "expansion", prompt_parent: "QueryExpansionPrompt" },
  },
  {
    name: "LLMQueryDecomposer",
    display_name: "Decomposer",
    description: "Independently retrievable sub-queries",
    metadata: {
      technique: "decomposition",
      prompt_parent: "QueryDecompositionPrompt",
    },
  },
];

const TRANSFORMATION_PROMPTS = [
  {
    name: "DefaultQueryRewritingPrompt",
    display_name: "Default Rewriting",
    description: "",
    metadata: { technique: "rewriting", variant: "default" },
  },
  {
    name: "DefaultQueryExpansionPrompt",
    display_name: "Default Expansion",
    description: "",
    metadata: { technique: "expansion", variant: "default" },
  },
  {
    name: "DefaultQueryDecompositionPrompt",
    display_name: "Default Decomposition",
    description: "",
    metadata: { technique: "decomposition", variant: "default" },
  },
];

const GENERATORS = [
  { name: "StubLLM", display_name: "Stub", description: "", downloaded: true },
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
  query_transformation: {
    section_name: "Transform",
    component: null,
    display_name: null,
    description: null,
    registered: false,
    params: [],
    enabled: false,
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
  api.getGeneratorComponents.mockResolvedValue(GENERATORS);
  api.getQueryTransformationComponents.mockResolvedValue(TRANSFORMERS);
  api.getQueryTransformationPrompts.mockResolvedValue(TRANSFORMATION_PROMPTS);
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
  for (const label of [
    "Chunking",
    "Transform",
    "Retrieval",
    "Model",
    "Prompt",
  ]) {
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

test("the sections sit two by two rather than in one scrolling row", async () => {
  await renderPanel();

  // The panel can be squeezed to 15% of the window and the labels come from the
  // backend -- Spanish "Fragmentación"/"Recuperación" is the worst case at 37
  // characters across five tabs. Five abreast either wrap or hide half of
  // themselves behind a scroll button; a two-column grid keeps every section
  // legible, with the fifth simply starting a new row.
  const tablist = screen.getByRole("tablist");
  const style = getComputedStyle(tablist);
  expect(style.display).toBe("grid");
  expect(style.gridTemplateColumns).toBe("repeat(2, 1fr)");

  expect(screen.getAllByRole("tab")).toHaveLength(5);
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

// ─── Query transformation stage ────────────────────────────────────────
// The optional stage is edited as a `{component, params}` reference; null is
// how the session (and the endpoint) represent it being off.

/** The transformation picker's root, scoped so hidden sections cannot leak in. */
function transformationPicker() {
  return screen.getByRole("switch").closest(".MuiStack-root");
}

test("a disabled query transformation shows its switch off and its technique cards", async () => {
  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));
  await screen.findByText("Rewriter");

  const picker = transformationPicker();
  expect(within(picker).getByRole("switch")).not.toBeChecked();
  for (const label of ["Rewriter", "Expander", "Decomposer"]) {
    expect(within(picker).getByText(label)).toBeInTheDocument();
  }
  // No technique is applied yet, so no card is ticked.
  expect(within(picker).queryByTestId("CheckIcon")).not.toBeInTheDocument();
});

test("choosing a technique enables the stage and ticks its card", async () => {
  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));
  const card = await screen.findByText("Expander");
  await userEvent.click(card);

  const picker = transformationPicker();
  await waitFor(() => expect(within(picker).getByRole("switch")).toBeChecked());
  expect(within(picker).getByTestId("CheckIcon")).toBeInTheDocument();
});

test("saving an enabled transformation PUTs the component reference", async () => {
  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));
  const card = await screen.findByText("Expander");
  await userEvent.click(card);

  const save = screen.getByRole("button", { name: /Save/i });
  await waitFor(() => expect(save).toBeEnabled());
  await userEvent.click(save);

  await waitFor(() =>
    expect(api.updateGenerativeSessionParams).toHaveBeenCalledTimes(1),
  );
  const [, sent] = api.updateGenerativeSessionParams.mock.calls[0];
  expect(sent.query_transformation).toEqual({
    component: "LLMQueryExpander",
    params: {
      llm_model: { component: "StubLLM", params: {} },
      prompt: {
        component: "DefaultQueryExpansionPrompt",
        params: { language: "en" },
      },
    },
  });
});

const DEFAULT_AWARE_GENERATORS = [
  {
    name: "FirstLLM",
    display_name: "First",
    description: "",
    downloaded: true,
  },
  {
    name: "Qwen25_15BInstruct",
    display_name: "Qwen 1.5B",
    description: "",
    downloaded: false,
  },
  { name: "LastLLM", display_name: "Last", description: "", downloaded: false },
];

/** The transformer schema the backend ships with the Qwen default declared. */
const TRANSFORMERS_WITH_SCHEMA = TRANSFORMERS.map((transformer) => ({
  ...transformer,
  schema: {
    properties: {
      llm_model: {
        placeholder: { component: "Qwen25_15BInstruct", params: {} },
      },
    },
  },
}));

test("enabling a technique seeds the schema-declared default model", async () => {
  api.getGeneratorComponents.mockResolvedValue(DEFAULT_AWARE_GENERATORS);
  api.getQueryTransformationComponents.mockResolvedValue(
    TRANSFORMERS_WITH_SCHEMA,
  );
  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));
  await userEvent.click(await screen.findByText("Expander"));

  const save = screen.getByRole("button", { name: /Save/i });
  await waitFor(() => expect(save).toBeEnabled());
  await userEvent.click(save);
  await waitFor(() =>
    expect(api.updateGenerativeSessionParams).toHaveBeenCalledTimes(1),
  );
  const [, sent] = api.updateGenerativeSessionParams.mock.calls[0];
  expect(sent.query_transformation.params.llm_model).toEqual({
    component: "Qwen25_15BInstruct",
    params: {},
  });
});

test("the seeded default falls back to the first downloaded model", async () => {
  api.getGeneratorComponents.mockResolvedValue([
    {
      name: "OtherLLM",
      display_name: "Other",
      description: "",
      downloaded: true,
    },
    {
      name: "AnotherLLM",
      display_name: "Another",
      description: "",
      downloaded: false,
    },
  ]);
  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));
  await userEvent.click(await screen.findByText("Expander"));

  const save = screen.getByRole("button", { name: /Save/i });
  await waitFor(() => expect(save).toBeEnabled());
  await userEvent.click(save);
  await waitFor(() =>
    expect(api.updateGenerativeSessionParams).toHaveBeenCalledTimes(1),
  );
  const [, sent] = api.updateGenerativeSessionParams.mock.calls[0];
  expect(sent.query_transformation.params.llm_model).toEqual({
    component: "OtherLLM",
    params: {},
  });
});

test("switching the transformation off then saving sends null", async () => {
  api.getRAGSession.mockResolvedValue({
    ...SESSION,
    parameters: {
      ...SESSION.parameters,
      query_transformation: {
        component: "LLMQueryExpander",
        params: {
          history_window: 2,
          llm_model: { component: "StubLLM", params: {} },
          prompt: {
            component: "DefaultQueryExpansionPrompt",
            params: { language: "en" },
          },
        },
      },
    },
  });
  api.getSessionConfiguration.mockResolvedValue({
    ...CONFIGURATION,
    query_transformation: {
      ...CONFIGURATION.query_transformation,
      component: "LLMQueryExpander",
      display_name: "Expander",
      registered: true,
      enabled: true,
    },
  });

  await renderPanel();
  await userEvent.click(screen.getByRole("tab", { name: /Transform/ }));

  const toggle = within(transformationPicker()).getByRole("switch");
  expect(toggle).toBeChecked();
  await userEvent.click(toggle);

  const save = screen.getByRole("button", { name: /Save/i });
  await waitFor(() => expect(save).toBeEnabled());
  await userEvent.click(save);

  await waitFor(() =>
    expect(api.updateGenerativeSessionParams).toHaveBeenCalledTimes(1),
  );
  const [, sent] = api.updateGenerativeSessionParams.mock.calls[0];
  expect(sent.query_transformation).toBeNull();
});
