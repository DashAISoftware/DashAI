import React from "react";
import { screen, waitFor, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import RAGSessionPage from "./RAGSessionPage";

// Indexing runs up front now, so this page owns when it starts and how long it
// keeps watching. Everything else on the page is mocked away: what is under
// test is that wiring, not the three-panel chrome.

jest.mock("react-router-dom", () => ({
  ...jest.requireActual("react-router-dom"),
  useParams: () => ({ id: "7" }),
  useNavigate: () => jest.fn(),
}));

jest.mock("../../../api/rag", () => ({
  RAG_TASK_NAME: "RAGTask",
  getSessionIndexStatus: jest.fn(),
  startSessionIndexing: jest.fn(),
}));

jest.mock("../../../api/generativeTask", () => ({
  getGenerativeSession: jest.fn(),
}));

jest.mock("../../../components/generative/GenerativeContext", () => ({
  useGenerative: () => ({
    sessions: [],
    selectedSessionId: 7,
    setSelectedSessionId: jest.fn(),
    setSelectedTaskName: jest.fn(),
    setSelectedDisplayName: jest.fn(),
    deleteSessionById: jest.fn(),
    fetchSessions: jest.fn(),
  }),
}));

jest.mock("../../../hooks/generative/useTaskDisplayName", () => ({
  useTaskDisplayName: () => "RAG",
}));

// The documents bar is the trigger under test: it reports every change that
// could invalidate the index through one callback.
jest.mock("../../../components/generative/RAG/DocumentsBar", () => {
  const MockDocumentsBar = ({ onDocumentChange, indexStatus }) => (
    <div>
      <button onClick={() => onDocumentChange?.()}>documents-changed</button>
      <span data-testid="bar-status">{indexStatus?.status ?? "none"}</span>
    </div>
  );
  return MockDocumentsBar;
});

jest.mock("../../../components/generative/RAG/RAGConfigPanel", () => {
  const MockConfigPanel = ({ onSaved }) => (
    <button onClick={() => onSaved?.()}>config-saved</button>
  );
  return MockConfigPanel;
});

jest.mock("../../../components/generative/GenerativeChat", () => {
  const MockChat = ({ indexStatus }) => (
    <div data-testid="chat-status">{indexStatus?.status ?? "none"}</div>
  );
  return MockChat;
});

jest.mock("../../../components/generative/SessionBar", () => {
  const MockSessionBar = () => null;
  return MockSessionBar;
});

jest.mock("../../../components/generative/RAG/RAGBreadcrumbs", () => {
  const MockBreadcrumbs = () => null;
  return MockBreadcrumbs;
});

const api = require("../../../api/rag");
const { getGenerativeSession } = require("../../../api/generativeTask");

const status = (value) => ({
  status: value,
  chunk_set_id: null,
  total_chunks: 0,
  retriever_ready: false,
  documents: [],
  message: `state: ${value}`,
  job_id: null,
  job: null,
});

beforeEach(() => {
  jest.clearAllMocks();
  getGenerativeSession.mockResolvedValue({ id: 7, name: "A session" });
  api.getSessionIndexStatus.mockResolvedValue(status("not_indexed"));
  api.startSessionIndexing.mockResolvedValue(status("indexing"));
});

afterEach(() => {
  jest.useRealTimers();
});

async function renderPage() {
  renderWithProviders(<RAGSessionPage />);
  await waitFor(() => expect(api.getSessionIndexStatus).toHaveBeenCalled());
}

test("reads the index status on open without starting a run", async () => {
  await renderPage();
  // Opening a session must not enqueue work; the read is safe to repeat.
  expect(api.startSessionIndexing).not.toHaveBeenCalled();
});

test("a document change starts indexing exactly once", async () => {
  await renderPage();

  await userEvent.click(screen.getByText("documents-changed"));

  // The documents bar batches a whole upload behind one callback. Starting a
  // run per file would rewrite the document set each time, and each rewrite
  // re-chunks and re-embeds every document.
  await waitFor(() =>
    expect(api.startSessionIndexing).toHaveBeenCalledTimes(1),
  );
  expect(api.startSessionIndexing).toHaveBeenCalledWith(7);
});

test("saving the configuration starts indexing too", async () => {
  await renderPage();

  await userEvent.click(screen.getByText("config-saved"));

  // Called unconditionally: the backend owns the rule for which settings
  // invalidate the index, and short-circuits when there is nothing to do.
  await waitFor(() =>
    expect(api.startSessionIndexing).toHaveBeenCalledTimes(1),
  );
});

test("the started run's status is shown without a further fetch", async () => {
  await renderPage();
  const readsBefore = api.getSessionIndexStatus.mock.calls.length;

  await userEvent.click(screen.getByText("documents-changed"));

  await waitFor(() =>
    expect(screen.getByTestId("bar-status")).toHaveTextContent("indexing"),
  );
  // The POST answers with the resulting status, so no follow-up GET is needed
  // to render it.
  expect(api.getSessionIndexStatus.mock.calls.length).toBe(readsBefore);
});

test("a failure to start still leaves the user with a status", async () => {
  api.startSessionIndexing.mockRejectedValue(new Error("boom"));
  jest.spyOn(console, "error").mockImplementation(() => {});
  await renderPage();
  const readsBefore = api.getSessionIndexStatus.mock.calls.length;

  await userEvent.click(screen.getByText("documents-changed"));

  await waitFor(() =>
    expect(api.getSessionIndexStatus.mock.calls.length).toBeGreaterThan(
      readsBefore,
    ),
  );
  console.error.mockRestore();
});

// Fake timers have to be installed before the page mounts, or the interval is
// scheduled against the real clock and never advances.
async function renderPageWithFakeTimers() {
  jest.useFakeTimers();
  renderWithProviders(<RAGSessionPage />);
  // Flush the mount effects and their promises without a timer-based waitFor,
  // which would deadlock against the fake clock.
  await act(async () => {});
}

test("polls while indexing and stops as soon as it is done", async () => {
  api.getSessionIndexStatus.mockResolvedValue(status("indexing"));
  await renderPageWithFakeTimers();
  expect(screen.getByTestId("chat-status")).toHaveTextContent("indexing");

  const during = api.getSessionIndexStatus.mock.calls.length;
  await act(async () => {
    jest.advanceTimersByTime(1600);
  });
  expect(api.getSessionIndexStatus.mock.calls.length).toBeGreaterThan(during);

  // Once the status leaves "indexing" the interval must clear itself, rather
  // than polling a finished job forever.
  api.getSessionIndexStatus.mockResolvedValue(status("indexed"));
  await act(async () => {
    jest.advanceTimersByTime(1600);
  });
  expect(screen.getByTestId("chat-status")).toHaveTextContent("indexed");

  const settled = api.getSessionIndexStatus.mock.calls.length;
  await act(async () => {
    jest.advanceTimersByTime(10000);
  });
  expect(api.getSessionIndexStatus.mock.calls.length).toBe(settled);
});

test("does not poll while the session is idle", async () => {
  // Default mock is "not_indexed": nothing is running, so nothing is watched.
  await renderPageWithFakeTimers();
  const before = api.getSessionIndexStatus.mock.calls.length;

  await act(async () => {
    jest.advanceTimersByTime(10000);
  });

  expect(api.getSessionIndexStatus.mock.calls.length).toBe(before);
});
