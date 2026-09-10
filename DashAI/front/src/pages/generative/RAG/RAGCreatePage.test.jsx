import React from "react";
import { screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import RAGCreatePage from "./RAGCreatePage";

// One stable object: an effect depends on `enqueueSnackbar`, so a fresh
// reference per render would restart it on every render.
jest.mock("notistack", () => {
  const snackbar = { enqueueSnackbar: jest.fn() };
  return { useSnackbar: () => snackbar };
});

jest.mock("../../../api/rag", () => ({
  RAG_TASK_NAME: "RAGTask",
  RAG_MODEL_NAME: "RAGPipeline",
  createRAGSession: jest.fn(),
  getGeneratorComponents: jest.fn(),
}));

// Jest only lets a mock factory close over `mock`-prefixed names.
const mockGenerative = {
  sessions: [],
  setSessions: jest.fn(),
  deleteSessionById: jest.fn(),
  tasks: [],
  taskDisplayNameMap: {},
};
jest.mock("../../../components/generative/GenerativeContext", () => ({
  useGenerative: () => mockGenerative,
}));

jest.mock("../../../components/credentials/credentialStatus", () => ({
  useCredentialStatuses: () => ({ statuses: {}, loaded: true }),
  // Same shape the real helper returns; the card reads the lists directly.
  getComponentCredentialState: () => ({
    requiredCredentials: [],
    optionalCredentials: [],
    credentialsSatisfied: true,
    locked: false,
    requiredPlatforms: "",
    optionalPlatforms: "",
  }),
}));

jest.mock("../../../hooks/generative/useTaskDisplayName", () => ({
  useTaskDisplayName: () => "RAG",
}));

// The session list is not what this page is being tested for, and it pulls in
// the whole generative context to render.
jest.mock("../../../components/generative/SessionBar", () => {
  const MockSessionBar = () => <div data-testid="session-bar" />;
  return MockSessionBar;
});

const api = require("../../../api/rag");

const MODELS = [
  {
    name: "StubLLM",
    display_name: "Stub LLM",
    description: "A model that needs nothing",
    metadata: { requires_download: false },
    downloaded: true,
  },
  {
    name: "OtherLLM",
    display_name: "Other LLM",
    description: "Another one",
    metadata: { requires_download: false },
    downloaded: true,
  },
];

beforeEach(() => {
  jest.clearAllMocks();
  api.getGeneratorComponents.mockResolvedValue(MODELS);
  api.createRAGSession.mockResolvedValue({ id: 7 });
});

test("loads the models instead of spinning forever", async () => {
  renderWithProviders(<RAGCreatePage />);

  // A regression guard: the effect that fetches the models was once deleted by
  // accident, leaving `loadingModels` true and the page on a permanent spinner.
  await waitFor(() => expect(api.getGeneratorComponents).toHaveBeenCalled());
  expect(await screen.findByText("Stub LLM")).toBeInTheDocument();
  expect(screen.getByText("Other LLM")).toBeInTheDocument();
  expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
});

test("does not tack a component count onto the form", async () => {
  renderWithProviders(<RAGCreatePage />);
  await screen.findByText("Stub LLM");

  // The picker's footer counts the options it is showing, which reads as
  // clutter on a two-field form.
  expect(screen.queryByText(/components available/i)).not.toBeInTheDocument();
  expect(screen.queryByText(/componentsAvailable/)).not.toBeInTheDocument();
});

test("suggests a session name so the form is ready to submit", async () => {
  renderWithProviders(<RAGCreatePage />);
  await screen.findByText("Stub LLM");

  const named = screen
    .getAllByRole("textbox")
    .some((input) => /RAG_Session/.test(input.value));
  expect(named).toBe(true);
});

test("a name and a model are enough to create, and no documents are sent", async () => {
  renderWithProviders(<RAGCreatePage />);
  await screen.findByText("Stub LLM");

  const create = screen.getByRole("button", { name: /create/i });
  expect(create).toBeDisabled();

  await userEvent.click(screen.getByText("Stub LLM"));
  await waitFor(() => expect(create).toBeEnabled());

  await userEvent.click(create);

  await waitFor(() => expect(api.createRAGSession).toHaveBeenCalledTimes(1));
  const payload = api.createRAGSession.mock.calls[0][0];
  expect(payload.task_name).toBe("RAGTask");
  expect(payload.parameters.generation_model.component).toBe("StubLLM");
  // Documents are uploaded into the session afterwards; sending them here is
  // rejected by the backend.
  expect(payload.parameters).not.toHaveProperty("documents");
});
