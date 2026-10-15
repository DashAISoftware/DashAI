import React from "react";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import RetrievalTracePanel from "./RetrievalTracePanel";

const REFERENCES = {
  "1_0": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 3,
    page: 2,
    text: "a",
  },
  "2_1": {
    document_id: 2,
    document_name: "Beta.pdf",
    document_position: 7,
    page: null,
    text: "b",
  },
  "1_3": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 5,
    page: 4,
    text: "c",
  },
  "1_2": {
    document_id: 1,
    document_name: "Alpha.pdf",
    document_position: 4,
    page: 4,
    text: "d",
  },
};

async function expandPanel() {
  await userEvent.click(screen.getByText("Retrieval trace"));
}

function badgeCount() {
  const label = screen.getByText("Retrieval trace");
  return within(label.parentElement).getByText(/\d+/);
}

test("renders the query count, node name and a resolved chunk", async () => {
  const trace = [
    {
      query: "q1",
      retriever: { name: "BM25Retriever", chunks: ["1_0"] },
    },
  ];

  renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  await expandPanel();

  expect(badgeCount()).toHaveTextContent("1");
  expect(screen.getByText("Query 1")).toBeInTheDocument();
  expect(screen.getByText("BM25Retriever")).toBeInTheDocument();
  expect(screen.getByText("Alpha.pdf")).toBeInTheDocument();
});

test("renders one query row per trace entry", async () => {
  const trace = [
    { query: "q1", retriever: { name: "BM25Retriever", chunks: [] } },
    { query: "q2", retriever: { name: "TFIDFRetriever", chunks: [] } },
  ];

  renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  await expandPanel();

  expect(badgeCount()).toHaveTextContent("2");
  expect(screen.getByText("Query 1")).toBeInTheDocument();
  expect(screen.getByText("Query 2")).toBeInTheDocument();
});

test("renders a parallel retriever's children nested under it", async () => {
  const trace = [
    {
      query: "q1",
      retriever: {
        name: "ParallelRetriever",
        chunks: ["1_0", "2_1"],
        children: [
          { name: "BM25Retriever", chunks: ["1_0"] },
          { name: "TFIDFRetriever", chunks: ["2_1"] },
        ],
      },
    },
  ];

  renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  await expandPanel();

  expect(screen.getByText("ParallelRetriever")).toBeInTheDocument();
  expect(screen.getByText("BM25Retriever")).toBeInTheDocument();
  expect(screen.getByText("TFIDFRetriever")).toBeInTheDocument();
});

test("renders cross-encoder scores when present", async () => {
  const trace = [
    {
      query: "q2",
      retriever: {
        name: "SentenceTransformerCrossEncoderRetriever",
        chunks: [],
        scores: [
          { ref: "1_3", score: 3.0 },
          { ref: "1_2", score: 2.0 },
        ],
      },
    },
  ];

  renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  await expandPanel();

  expect(screen.getByText("Scores")).toBeInTheDocument();
  // Scores render rounded to three decimals for readability.
  expect(screen.getByText("1_3: 3.000")).toBeInTheDocument();
  expect(screen.getByText("1_2: 2.000")).toBeInTheDocument();
});

test("falls back to the raw ref when it is missing from references", async () => {
  const trace = [
    { query: "q1", retriever: { name: "CascadeRetriever", chunks: ["9_9"] } },
  ];

  renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  await expandPanel();

  expect(screen.getByText("9_9")).toBeInTheDocument();
});

test.each([
  ["null", null],
  ["undefined", undefined],
  ["empty", []],
  ["not an array", { query: "q1" }],
])("returns null when the trace is %s", (_, trace) => {
  const { container } = renderWithProviders(
    <RetrievalTracePanel trace={trace} references={REFERENCES} />,
  );
  expect(container.firstChild).toBeNull();
});

test("renders raw refs without crashing when references are absent", async () => {
  const trace = [
    { query: "q1", retriever: { name: "BM25Retriever", chunks: ["1_0"] } },
  ];

  renderWithProviders(<RetrievalTracePanel trace={trace} />);
  await expandPanel();

  expect(screen.getByText("1_0")).toBeInTheDocument();
});
