import React from "react";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import { getComponents } from "../../../api/component";
import { useExplorersAndConverters } from "../../notebooks/context/ExplorersAndConvertersContext";

jest.mock("../../../api/component", () => ({
  getComponents: jest.fn(),
}));

jest.mock("../../notebooks/context/ExplorersAndConvertersContext", () => ({
  useExplorersAndConverters: jest.fn(),
}));

import AppliedConvertersView from "./AppliedConvertersView";

const renderView = (props) =>
  renderWithProviders(<AppliedConvertersView {...props} />);

const makeDataTransfer = (payload) => ({
  types: payload ? ["application/x-dashai-tool"] : [],
  getData: () => (payload ? JSON.stringify(payload) : ""),
  dropEffect: "none",
});

const AVAILABLE_CONVERTERS = [
  {
    name: "Binarizer",
    display_name: "Binarizador",
    description: "Binariza datos.",
    metadata: { output_type: "Integer" },
  },
  {
    name: "BagOfWordsConverter",
    display_name: "Bag of Words",
    description: "Bolsa de palabras.",
    metadata: { output_type: "Integer" },
  },
];

const datasetTypes = { age: { type: "Integer" }, text: { type: "Text" } };

describe("AppliedConvertersView", () => {
  let setPendingDropTool;

  beforeEach(() => {
    getComponents.mockResolvedValue(AVAILABLE_CONVERTERS);
    setPendingDropTool = jest.fn();
    useExplorersAndConverters.mockReturnValue({ setPendingDropTool });
  });

  it("shows a message when there are no converters", () => {
    renderView({
      newExp: { preprocessing: [] },
      setNewExp: () => {},
      datasetTypes,
    });

    expect(screen.getByText("No converter was added.")).toBeInTheDocument();
  });

  it("shows a converter's real display name, scope and output type chip", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "Binarizer",
          params: { threshold: 0.5 },
          scope: [{ kind: "raw", name: "age" }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
      ],
    };

    renderView({ newExp, setNewExp: () => {}, datasetTypes });

    expect(await screen.findByText("Binarizador")).toBeInTheDocument();
    expect(screen.getByText("age")).toBeInTheDocument();
    expect(screen.getByText("Binarizador: output")).toBeInTheDocument();
    expect(screen.getAllByText("Integer").length).toBeGreaterThan(0);
  });

  it("shows a chained converter's scope as the earlier converter's output group", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          params: {},
          scope: [{ kind: "raw", name: "text" }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "group", step: 0 }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
      ],
    };

    renderView({ newExp, setNewExp: () => {}, datasetTypes });

    await screen.findByText("Bag of Words");
    // The second card's scope shows the first converter's output label.
    expect(screen.getAllByText("Bag of Words: output").length).toBe(2);
  });

  it("shows one chip per declared slot when a step's scope mixed column types", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "SimpleImputer",
          params: { strategy: "most_frequent" },
          scope: [
            { kind: "raw", name: "age" },
            { kind: "raw", name: "text" },
          ],
          outputSlots: [
            { slot: "Integer", type: "Integer", dtype: "int64" },
            { slot: "Categorical", type: "Categorical", dtype: null },
          ],
        },
      ],
    };

    renderView({
      newExp,
      setNewExp: () => {},
      datasetTypes: {
        ...datasetTypes,
        // "SimpleImputer" isn't in AVAILABLE_CONVERTERS, so its display
        // name falls back to the raw converter name — fine here, this
        // test only cares about the output chips.
      },
    });

    // No "(slot)" suffix: each slot already gets its own colored type chip
    // (asserted below), so both chips share the same label text.
    expect(await screen.findAllByText("SimpleImputer: output")).toHaveLength(2);
    expect(screen.getByText("Integer")).toBeInTheDocument();
    expect(screen.getByText("Categorical")).toBeInTheDocument();
  });

  it("numbers two converters of the same type so their cards and output labels don't collide", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "Binarizer",
          params: { threshold: 0.5 },
          scope: [{ kind: "raw", name: "age" }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
        {
          converter: "Binarizer",
          params: { threshold: 1 },
          scope: [{ kind: "raw", name: "text" }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
      ],
    };

    renderView({ newExp, setNewExp: () => {}, datasetTypes });

    expect(await screen.findByText("Binarizador")).toBeInTheDocument();
    expect(screen.getByText("Binarizador (2)")).toBeInTheDocument();
    expect(screen.getByText("Binarizador: output")).toBeInTheDocument();
    expect(screen.getByText("Binarizador (2): output")).toBeInTheDocument();
  });

  it("cascades deletion to every converter configured after the deleted one", async () => {
    const setNewExp = jest.fn();
    const newExp = {
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          params: {},
          scope: [{ kind: "raw", name: "text" }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "group", step: 0 }],
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
      ],
    };

    renderView({ newExp, setNewExp, datasetTypes });

    await screen.findByText("Bag of Words");
    const deleteButtons = screen.getAllByRole("button", { name: "Remove" });
    fireEvent.click(deleteButtons[0]);

    // Deleting the first converter cascades to the second (its scope
    // references the first one's output group), so the confirmation modal
    // must warn about both before anything is actually removed.
    expect(
      await screen.findByText("The following items will be deleted:"),
    ).toBeInTheDocument();
    expect(setNewExp).not.toHaveBeenCalled();

    fireEvent.click(screen.getByRole("button", { name: "Delete" }));

    expect(setNewExp).toHaveBeenCalledWith({
      ...newExp,
      preprocessing: [],
    });
  });

  it("hands a dropped tool off to setPendingDropTool, just like Notebooks' drop target", () => {
    renderView({
      newExp: { preprocessing: [] },
      setNewExp: () => {},
      datasetTypes,
    });

    const dropZone = screen.getByText("No converter was added.").parentElement;
    const tool = { name: "Binarizer", display_name: "Binarizador" };
    fireEvent.drop(dropZone, { dataTransfer: makeDataTransfer(tool) });

    expect(setPendingDropTool).toHaveBeenCalledWith(tool);
  });

  it("ignores a drop with no recognizable tool payload", () => {
    renderView({
      newExp: { preprocessing: [] },
      setNewExp: () => {},
      datasetTypes,
    });

    const dropZone = screen.getByText("No converter was added.").parentElement;
    fireEvent.drop(dropZone, { dataTransfer: makeDataTransfer(null) });

    expect(setPendingDropTool).not.toHaveBeenCalled();
  });
});
