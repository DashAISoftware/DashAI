import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import RAGChatProgress from "./RAGChatProgress";

// renderWithProviders initializes i18n with the fallback language "en", so the
// assertions below use the English strings from generative.json.

test("renders the transforming stage message", () => {
  renderWithProviders(<RAGChatProgress progress={{ stage: "transforming" }} />);

  expect(screen.getByText("Transforming query…")).toBeInTheDocument();
});

test("renders the retrieving stage with the queries joined by '; '", () => {
  renderWithProviders(
    <RAGChatProgress progress={{ stage: "retrieving", queries: ["a", "b"] }} />,
  );

  expect(
    screen.getByText("Searching sources with query: a; b"),
  ).toBeInTheDocument();
});

test("renders the generating stage message", () => {
  renderWithProviders(<RAGChatProgress progress={{ stage: "generating" }} />);

  expect(
    screen.getByText("Using sources to generate the answer"),
  ).toBeInTheDocument();
});

test("renders nothing for a null progress", () => {
  const { container } = renderWithProviders(
    <RAGChatProgress progress={null} />,
  );

  expect(container).toBeEmptyDOMElement();
});
