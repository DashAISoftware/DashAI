import React from "react";
import { screen, within, act } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import SourcesDisplay from "./SourcesDisplay";

// WS-A owns the real TraceChunksModal; mock the module with a stub that records
// and exposes its props so this test stays independent of the modal's internals.
jest.mock("./RAG/TraceChunksModal", () => {
  const ReactModule = require("react");
  const calls = [];
  const StubTraceChunksModal = (props) => {
    calls.push(props);
    return ReactModule.createElement("div", {
      "data-testid": "stub-modal",
      "data-open": String(props.open),
      "data-trace": JSON.stringify(props.trace ?? null),
      "data-user": String(props.userMessage ?? ""),
    });
  };
  StubTraceChunksModal.calls = calls;
  return { __esModule: true, default: StubTraceChunksModal };
});

const TraceChunksModal = jest.requireMock("./RAG/TraceChunksModal").default;

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

function renderSources() {
  return renderWithProviders(
    <SourcesDisplay
      references={REFERENCES}
      trace={TRACE}
      userMessage={USER_MESSAGE}
    />,
  );
}

function lastProps() {
  return TraceChunksModal.calls.at(-1);
}

beforeEach(() => {
  TraceChunksModal.calls.length = 0;
});

test("renders the header, document count and a single view button", () => {
  renderSources();

  const label = screen.getByText("View message sources");
  expect(within(label.parentElement).getByText("2")).toBeInTheDocument();
  expect(screen.getAllByRole("button", { name: /view chunks/i })).toHaveLength(
    1,
  );

  // No per-document rows from the legacy expandable list.
  expect(screen.queryByText("Alpha.pdf")).not.toBeInTheDocument();
  expect(screen.queryByText("Beta.pdf")).not.toBeInTheDocument();
});

test("opens the modal with the trace, references and user message", async () => {
  renderSources();

  expect(lastProps().open).toBe(false);

  await userEvent.click(screen.getByRole("button", { name: /view chunks/i }));

  const props = lastProps();
  expect(props.open).toBe(true);
  expect(props.trace).toEqual(TRACE);
  expect(props.references).toEqual(REFERENCES);
  expect(props.userMessage).toBe(USER_MESSAGE);
  expect(screen.getByTestId("stub-modal")).toHaveAttribute("data-open", "true");
});

test("closes the modal again through onClose", async () => {
  renderSources();

  await userEvent.click(screen.getByRole("button", { name: /view chunks/i }));
  expect(screen.getByTestId("stub-modal")).toHaveAttribute("data-open", "true");

  act(() => {
    lastProps().onClose();
  });

  expect(lastProps().open).toBe(false);
  expect(screen.getByTestId("stub-modal")).toHaveAttribute(
    "data-open",
    "false",
  );
});
