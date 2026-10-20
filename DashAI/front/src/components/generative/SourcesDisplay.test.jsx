import React from "react";
import { screen, within, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import SourcesDisplay from "./SourcesDisplay";
import { TRACE_VIEW_CHUNKS, TRACE_VIEW_PIPELINE } from "../../constants/rag";

// Mock the panel module with a stub that records props so this test focuses on
// SourcesDisplay's toggle wiring.
jest.mock("./RAG/TraceChunksPanel", () => {
  const ReactModule = require("react");
  const calls = [];
  const StubTraceChunksPanel = (props) => {
    calls.push(props);
    return ReactModule.createElement("div", {
      "data-testid": "stub-panel",
      "data-view": String(props.activeView),
      "data-trace": JSON.stringify(props.trace ?? null),
      "data-user": String(props.userMessage ?? ""),
    });
  };
  StubTraceChunksPanel.calls = calls;
  return {
    __esModule: true,
    default: StubTraceChunksPanel,
  };
});

const TraceChunksPanel = jest.requireMock("./RAG/TraceChunksPanel").default;

// Two distinct documents (ids 1 and 2) across three chunks.
const REFERENCES = {
  "1_0": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 1,
    page: 2,
    text: "a",
  },
  "2_1": {
    document_id: 2,
    document_name: "Beta.pdf",
    document_position: 2,
    page: null,
    text: "b",
  },
  "1_3": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 3,
    page: 4,
    text: "c",
  },
};

const TRACE = [
  { query: "q1", retriever: { name: "BM25Retriever", chunks: ["1_0"] } },
  { query: "q2", retriever: { name: "TFIDFRetriever", chunks: ["2_1"] } },
];

const USER_MESSAGE = "What is X?";

function renderSources(overrides = {}) {
  return renderWithProviders(
    <SourcesDisplay
      references={REFERENCES}
      trace={TRACE}
      userMessage={USER_MESSAGE}
      {...overrides}
    />,
  );
}

function lastProps() {
  return TraceChunksPanel.calls.at(-1);
}

const chunksButton = () => screen.getByRole("button", { name: "Chunks" });
const pipelineButton = () => screen.getByRole("button", { name: "Pipeline" });

beforeEach(() => {
  TraceChunksPanel.calls.length = 0;
});

test("renders the header, document count and both toggles without a panel", () => {
  renderSources();

  const label = screen.getByText("View message sources");
  expect(within(label.parentElement).getByText("2")).toBeInTheDocument();
  expect(chunksButton()).toBeInTheDocument();
  expect(pipelineButton()).toBeInTheDocument();
  expect(screen.queryByTestId("stub-panel")).not.toBeInTheDocument();

  // No per-document rows from the legacy expandable list.
  expect(screen.queryByText("Alpha.pdf")).not.toBeInTheDocument();
  expect(screen.queryByText("Beta.pdf")).not.toBeInTheDocument();
});

test("opens the inline panel on the chunks view with the answer data", async () => {
  renderSources();

  await userEvent.click(chunksButton());

  const props = lastProps();
  expect(props.activeView).toBe(TRACE_VIEW_CHUNKS);
  expect(props.trace).toEqual(TRACE);
  expect(props.references).toEqual(REFERENCES);
  expect(props.userMessage).toBe(USER_MESSAGE);
  expect(screen.getByTestId("stub-panel")).toHaveAttribute(
    "data-view",
    TRACE_VIEW_CHUNKS,
  );
});

test("switches the same panel to the pipeline view", async () => {
  renderSources();

  await userEvent.click(chunksButton());
  await userEvent.click(pipelineButton());

  expect(screen.getAllByTestId("stub-panel")).toHaveLength(1);
  expect(lastProps().activeView).toBe(TRACE_VIEW_PIPELINE);
  expect(screen.getByTestId("stub-panel")).toHaveAttribute(
    "data-view",
    TRACE_VIEW_PIPELINE,
  );
});

test("clicking the active toggle again closes the panel", async () => {
  renderSources();

  await userEvent.click(chunksButton());
  expect(screen.getByTestId("stub-panel")).toBeInTheDocument();

  await userEvent.click(chunksButton());
  expect(screen.queryByTestId("stub-panel")).not.toBeInTheDocument();
});

test("closing through the panel onClose removes it", async () => {
  renderSources();

  await userEvent.click(pipelineButton());
  expect(screen.getByTestId("stub-panel")).toBeInTheDocument();

  act(() => {
    lastProps().onClose();
  });

  expect(screen.queryByTestId("stub-panel")).not.toBeInTheDocument();
});

test("marks the pipeline toggle as disabled when the trace has no renderable entries", async () => {
  renderSources({ trace: [] });

  expect(chunksButton()).toBeEnabled();
  expect(pipelineButton()).toHaveAttribute("aria-disabled", "true");

  await userEvent.click(pipelineButton());
  expect(screen.queryByTestId("stub-panel")).not.toBeInTheDocument();
});
