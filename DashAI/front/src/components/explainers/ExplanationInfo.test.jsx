import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";

import ExplanationInfo from "./ExplanationInfo";

// `outputColumns` comes straight off `model_session.output_columns`, which
// is always a list of column *atoms* since converter output groups landed.
// Rendering one of those objects directly into a `<Chip label>` crashed the
// whole explainer wizard with "Objects are not valid as a React child".
describe("ExplanationInfo", () => {
  it("renders atom-shaped output columns as their column name", () => {
    renderWithProviders(
      <ExplanationInfo
        inputColumns={["SepalLengthCm", "SepalWidthCm"]}
        outputColumns={[{ kind: "column", name: "Species" }]}
      />,
    );
    expect(screen.getByText("Species")).toBeInTheDocument();
    expect(screen.getByText("SepalLengthCm")).toBeInTheDocument();
  });

  it("still renders legacy plain-string columns", () => {
    renderWithProviders(
      <ExplanationInfo inputColumns={["text"]} outputColumns={["label"]} />,
    );
    expect(screen.getByText("label")).toBeInTheDocument();
  });

  it("renders a group atom as its source converter, not as an object", () => {
    renderWithProviders(
      <ExplanationInfo
        inputColumns={[]}
        outputColumns={[{ kind: "group", converter_id: "conv_0", slot: 0 }]}
        converters={[{ id: "conv_0", converter: "BagOfWords" }]}
      />,
    );
    expect(screen.getByText("BagOfWords: 0")).toBeInTheDocument();
  });
});
