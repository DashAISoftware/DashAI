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

const column = (name, type, origin) => ({
  kind: "column",
  name,
  type,
  dtype: null,
  origin,
});

const block = (step, slot, type, count) => ({
  kind: "block",
  step,
  slot,
  label: "output",
  type,
  dtype: null,
  count,
});

const okStep = (added) => ({
  status: "ok",
  state: [],
  added,
  error: null,
  warnings: [],
});

const structureOf = (steps) => ({ initial: [], steps, final: [], valid: true });

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
    });

    expect(screen.getByText("No converter was added.")).toBeInTheDocument();
  });

  it("shows a converter's real display name, scope and estimated output", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "Binarizer",
          params: { threshold: 0.5 },
          scope: [{ kind: "raw", name: "age" }],
        },
      ],
    };
    const structure = structureOf([okStep([column("bin_age", "Integer", 0)])]);

    renderView({ newExp, setNewExp: () => {}, structure });

    expect(await screen.findByText("Binarizador")).toBeInTheDocument();
    expect(screen.getByText("age")).toBeInTheDocument();
    expect(screen.getAllByText("bin_age").length).toBeGreaterThan(0);
    expect(screen.getAllByText("Integer").length).toBeGreaterThan(0);
  });

  it("shows a chained converter's scope as the earlier converter's output", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          params: {},
          scope: [{ kind: "raw", name: "text" }],
        },
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "group", step: 0 }],
        },
      ],
    };
    const structure = structureOf([
      okStep([block(0, null, "Integer", null)]),
      okStep([block(1, null, "Integer", null)]),
    ]);

    renderView({ newExp, setNewExp: () => {}, structure });

    await screen.findByText("Bag of Words");
    // The second card's scope names the first converter's output.
    expect(screen.getByText("Bag of Words: output")).toBeInTheDocument();
    // Each card's output block shows its size, N when unknown.
    expect(screen.getAllByText("Bag of Words: output (N columns)").length).toBe(
      1,
    );
  });

  it("shows one chip per estimated block when a step's output mixes types", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "SelectKBest",
          params: { k: 1 },
          scope: [
            { kind: "raw", name: "age" },
            { kind: "raw", name: "score" },
          ],
        },
      ],
    };
    const structure = structureOf([
      okStep([
        block(0, "Integer", "Integer", null),
        block(0, "Float", "Float", null),
      ]),
    ]);

    renderView({ newExp, setNewExp: () => {}, structure });

    expect(
      await screen.findAllByText("SelectKBest: output (N columns)"),
    ).toHaveLength(2);
    expect(screen.getByText("Float")).toBeInTheDocument();
  });

  it("numbers two converters of the same type so their cards don't collide", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "Binarizer",
          params: { threshold: 0.5 },
          scope: [{ kind: "raw", name: "age" }],
        },
        {
          converter: "Binarizer",
          params: { threshold: 1 },
          scope: [{ kind: "raw", name: "text" }],
        },
      ],
    };

    renderView({ newExp, setNewExp: () => {}, structure: null });

    expect(await screen.findByText("Binarizador")).toBeInTheDocument();
    expect(screen.getByText("Binarizador (2)")).toBeInTheDocument();
  });

  it("flags a step that cannot work and dims the ones after it", async () => {
    const newExp = {
      preprocessing: [
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "raw", name: "age" }],
        },
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "raw", name: "text" }],
        },
      ],
    };
    const structure = {
      ...structureOf([]),
      valid: false,
      steps: [
        {
          status: "error",
          state: [],
          added: [],
          error: { code: "missing_ref", params: { ref: "age" } },
          warnings: [],
        },
        { status: "blocked", state: [], added: [], error: null, warnings: [] },
      ],
    };

    renderView({ newExp, setNewExp: () => {}, structure });

    expect(
      await screen.findByText(
        '"age" does not exist at this point of the chain: an earlier step may have consumed it.',
      ),
    ).toBeInTheDocument();
    expect(screen.getByTestId("session-converter-card-0")).toHaveAttribute(
      "data-status",
      "error",
    );
    expect(screen.getByTestId("session-converter-card-1")).toHaveAttribute(
      "data-status",
      "blocked",
    );
    expect(
      screen.getByText("Fix the previous step to check this one."),
    ).toBeInTheDocument();
  });

  it("shows the dataset state after the whole chain", async () => {
    const structure = {
      ...structureOf([]),
      final: [column("age", "Integer", null), block(0, null, "Float", 2)],
    };

    renderView({
      newExp: { preprocessing: [] },
      setNewExp: () => {},
      structure,
    });

    expect(
      await screen.findByText("Dataset after preprocessing"),
    ).toBeInTheDocument();
    expect(screen.getByText("age")).toBeInTheDocument();
  });

  it("cascades deletion to every converter configured after the deleted one", async () => {
    const setNewExp = jest.fn();
    const newExp = {
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          params: {},
          scope: [{ kind: "raw", name: "text" }],
        },
        {
          converter: "Binarizer",
          params: {},
          scope: [{ kind: "group", step: 0 }],
        },
      ],
    };

    renderView({ newExp, setNewExp, structure: null });

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
    });

    const dropZone = screen.getByText("No converter was added.").parentElement;
    fireEvent.drop(dropZone, { dataTransfer: makeDataTransfer(null) });

    expect(setPendingDropTool).not.toHaveBeenCalled();
  });
});
