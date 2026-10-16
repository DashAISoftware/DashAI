import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import GenerativeChat from "./GenerativeChat";

// What is under test is the in-flight render gate: an in-flight RAG message
// with a resolvable `progress` payload shows the live stage line, while a
// payload the helper cannot render (unknown stage, bad queries) must fall back
// to the generic waiting bubble instead of leaving the row blank. Everything
// the chat fetches is mocked; only the render branching is real.

jest.mock("../../api/process", () => ({
  getProcessById: jest.fn(),
  getProcessesBySessionId: jest.fn(),
  deleteProcessById: jest.fn(),
  postProcess: jest.fn(),
}));

jest.mock("../../api/job", () => ({
  enqueueGenerativeProcessJob: jest.fn(),
  startJobQueue: jest.fn(),
}));

jest.mock("../../api/session", () => ({
  getHistoryBySessionId: jest.fn(),
  getSessionById: jest.fn(),
}));

jest.mock("../../api/component", () => ({
  getComponentById: jest.fn(),
  getComponentDownloadStatus: jest.fn(),
}));

jest.mock("../../api/generativeTask", () => ({
  getRelatedComponents: jest.fn(),
}));

jest.mock("./GenerativeContext", () => ({
  useGenerative: () => ({
    selectedSessionId: 7,
    selectedTaskName: "RAGTask",
    tasks: [],
    paramsVersion: 0,
    setParamsVersion: jest.fn(),
    fetchSessions: jest.fn(),
  }),
}));

jest.mock("../models/model/ComponentDownloadControl", () => {
  const MockControl = () => null;
  MockControl.useComponentDownloadState = () => ({
    downloaded: true,
    downloading: false,
  });
  return MockControl;
});

jest.mock("../credentials/credentialStatus", () => ({
  useCredentialStatuses: () => ({ statuses: {}, loaded: true }),
  getComponentCredentialState: () => ({
    locked: false,
    requiredPlatforms: [],
  }),
}));

jest.mock("notistack", () => ({
  useSnackbar: () => ({ enqueueSnackbar: jest.fn() }),
}));

// ChatBubble's subtree pulls ESM-only deps Jest cannot parse; the branch under
// test only needs to distinguish "waiting bubble shown" from "status line".
jest.mock("./ChatBubble", () => {
  const MockChatBubble = ({ isWaiting }) => (
    <div data-testid={isWaiting ? "waiting-bubble" : "answer-bubble"} />
  );
  return { ChatBubble: MockChatBubble };
});

jest.mock("./MediaInput", () => ({
  MediaInput: () => <div data-testid="media-input" />,
}));

jest.mock("../jobs/JobQueueWidget", () => () => null);
jest.mock("../custom/TemplateModal", () => () => null);
jest.mock("./InfoSessionModal", () => () => null);
jest.mock("./ModelSwitcher", () => () => null);
jest.mock("../credentials/CredentialsDialog", () => () => null);
jest.mock("./SourcesDisplay", () => () => null);

const { getProcessesBySessionId } = require("../../api/process");
const { getSessionById } = require("../../api/session");
const { getHistoryBySessionId } = require("../../api/session");
const { getRelatedComponents } = require("../../api/generativeTask");
const {
  getComponentById,
  getComponentDownloadStatus,
} = require("../../api/component");
const { getProcessById } = require("../../api/process");

const inFlightProcess = (progress) => ({
  id: "11",
  created: "2026-10-16T10:00:00",
  last_modified: "2026-10-16T10:00:05",
  start_time: "2026-10-16T10:00:01",
  end_time: null,
  status: 2,
  session_id: 7,
  delivery_time: null,
  progress,
  input: [
    { id: 1, process_id: 11, data: "hi", data_type: "str", is_input: true },
  ],
  output: [],
});

beforeEach(() => {
  jest.clearAllMocks();
  getSessionById.mockResolvedValue({
    id: 7,
    name: "S",
    task_name: "RAGTask",
  });
  getHistoryBySessionId.mockResolvedValue([]);
  getRelatedComponents.mockResolvedValue([]);
  getComponentById.mockResolvedValue({ name: "M", metadata: {} });
  getComponentDownloadStatus.mockResolvedValue({ downloaded: true });
  getProcessById.mockImplementation((id) =>
    Promise.resolve(inFlightProcess({ stage: "generating" })),
  );
});

const renderChat = (process) => {
  getProcessesBySessionId.mockResolvedValue([process]);
  renderWithProviders(<GenerativeChat indexStatus={{ status: "ready" }} />);
};

test("in-flight RAG message with a resolvable stage shows the status line", async () => {
  renderChat(
    inFlightProcess({ stage: "retrieving", queries: ["alpha", "beta"] }),
  );
  // findBy*: the messages arrive through a resolved promise.
  expect(
    await screen.findByText("Searching sources with query: alpha; beta"),
  ).toBeInTheDocument();
  expect(screen.queryByTestId("waiting-bubble")).not.toBeInTheDocument();
});

test("in-flight RAG message with an unresolvable payload falls back to the waiting bubble", async () => {
  renderChat(inFlightProcess({ stage: "something-new" }));
  // The waiting bubble only renders inside a loaded message row, so finding it
  // also proves the process data made it into the tree.
  expect(await screen.findByTestId("waiting-bubble")).toBeInTheDocument();
  expect(
    screen.queryByText(/Searching sources with query/),
  ).not.toBeInTheDocument();
});

test("in-flight RAG message without progress falls back to the waiting bubble", async () => {
  renderChat(inFlightProcess(null));
  expect(await screen.findByTestId("waiting-bubble")).toBeInTheDocument();
  expect(
    screen.queryByText(/Searching sources with query/),
  ).not.toBeInTheDocument();
});
