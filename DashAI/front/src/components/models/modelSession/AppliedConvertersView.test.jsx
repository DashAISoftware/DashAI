import React from "react";
import { screen, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";

jest.mock("../../../api/component", () => ({
  getComponentById: jest.fn(),
  getComponents: jest.fn(),
}));

jest.mock("../../../api/modelSession", () => ({
  getConvertersOutputSlots: jest.fn(),
}));

import { getComponentById, getComponents } from "../../../api/component";
import { getConvertersOutputSlots } from "../../../api/modelSession";
import AppliedConvertersView from "./AppliedConvertersView";

const converterTools = [
  {
    name: "PCA",
    display_name: "Principal Component Analysis",
    metadata: {
      output_slots: [
        { slot: "pca_0", label: "PC 1" },
        { slot: "pca_1", label: "PC 2" },
      ],
    },
  },
  { name: "StandardScaler", display_name: "Standard Scaler", metadata: {} },
];

beforeEach(() => {
  getComponentById.mockImplementation((name) =>
    Promise.resolve(
      converterTools.find((tool) => tool.name === name) || { name },
    ),
  );
  getComponents.mockResolvedValue(converterTools);
  getConvertersOutputSlots.mockResolvedValue({
    conv_0: [{ slot: 0, label: "output", type: "Float" }],
    conv_1: [{ slot: 0, label: "output", type: "Float" }],
  });
});

const session = {
  converters: [
    {
      id: "conv_0",
      converter: "PCA",
      params: { n_components: 2 },
      input_scope: [{ kind: "column", name: "SepalLengthCm" }],
      target_column: null,
    },
    {
      id: "conv_1",
      converter: "StandardScaler",
      params: {},
      input_scope: [{ kind: "group", converter_id: "conv_0", slot: "pca_0" }],
      target_column: null,
    },
  ],
};

describe("AppliedConvertersView (smoke)", () => {
  it("renders a column-scoped and a group-scoped converter card without crashing", async () => {
    renderWithProviders(
      <AppliedConvertersView session={session} onRemoveConverter={() => {}} />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("Principal Component Analysis: PC 1"),
      ).toBeInTheDocument(),
    );
    expect(screen.getAllByText("SepalLengthCm").length).toBeGreaterThan(0);
  });

  it("shows each converter's real output slot(s) as chips, not a status dot", async () => {
    renderWithProviders(
      <AppliedConvertersView session={session} onRemoveConverter={() => {}} />,
    );
    await waitFor(() =>
      expect(
        screen.getByText("Principal Component Analysis: output"),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Standard Scaler: output")).toBeInTheDocument();
    expect(screen.getAllByText("Float").length).toBe(2);
  });
});
