import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import { getComponents } from "../../../api/component";

// react-markdown ships ESM only and Create React App's jest does not transform
// node_modules, so importing PreprocessingStep (which transitively imports the
// converter parameter form, all the way down to FormTooltip) pulls in a parse
// error before a single assertion runs. Same stub used elsewhere in this repo
// (e.g. FormSchemaRenderFields.test.jsx) for the same reason.
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

jest.mock("../../../api/component", () => ({
  getComponents: jest.fn(),
}));

jest.mock("../ModelsContext", () => ({
  useModels: () => ({ setSessionRightContent: () => {} }),
}));

jest.mock("../../notebooks/context/ExplorersAndConvertersContext", () => ({
  useExplorersAndConverters: () => ({ setPendingDropTool: () => {} }),
}));

import PreprocessingStep from "./PreprocessingStep";

describe("PreprocessingStep", () => {
  beforeEach(() => {
    getComponents.mockResolvedValue([]);
  });

  it("shows a message when no converter has been added yet", async () => {
    renderWithProviders(
      <PreprocessingStep
        newExp={{ preprocessing: [] }}
        setNewExp={() => {}}
        setNextEnabled={() => {}}
        datasetInfo={{ column_names: [] }}
        datasetTypes={{}}
      />,
    );

    expect(
      await screen.findByText("No converter was added."),
    ).toBeInTheDocument();
  });
});
