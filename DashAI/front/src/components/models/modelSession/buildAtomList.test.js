import {
  buildAtomList,
  atomKey,
  realAtomKey,
  toRealAtom,
  reseedColumnSelection,
  isAtomSelectionValidLocally,
} from "./buildAtomList";

describe("buildAtomList", () => {
  it("includes every raw dataset column", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: { a: { type: "Float", dtype: "float64" } },
      converters: [],
    });
    expect(atoms).toEqual([
      { kind: "column", name: "a", type: "Float", dtype: "float64" },
    ]);
  });

  it("adds one atom per declared slot of each configured converter", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: { a: { type: "Float", dtype: "float64" } },
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "output" }] },
        },
      ],
    });
    expect(atoms).toContainEqual({
      kind: "group",
      converterId: "conv_0",
      slot: 0,
      label: "output",
      converterName: "StandardScaler",
    });
  });

  it("carries a group atom's declared type through from output_slots", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: {},
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: {
            output_slots: [{ slot: 0, label: "output", type: "Float" }],
          },
        },
      ],
    });
    expect(atoms).toContainEqual({
      kind: "group",
      converterId: "conv_0",
      slot: 0,
      label: "output",
      converterName: "StandardScaler",
      type: "Float",
    });
  });

  it("adds one atom per slot for a converter with multiple slots", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: {},
      converters: [
        {
          id: "conv_0",
          converter: "SimpleImputer",
          metadata: {
            output_slots: [
              { slot: 0, label: "imputed" },
              { slot: 1, label: "missing_indicator" },
            ],
          },
        },
      ],
    });
    expect(atoms.filter((a) => a.kind === "group")).toHaveLength(2);
  });

  it("never removes an earlier atom, even after later converters are added", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: { a: { type: "Float", dtype: "float64" } },
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "output" }] },
        },
        {
          id: "conv_1",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "output" }] },
        },
      ],
    });
    expect(atoms).toContainEqual(
      expect.objectContaining({ kind: "column", name: "a" }),
    );
    expect(atoms.filter((a) => a.kind === "group")).toHaveLength(2);
  });
});

describe("atomKey / realAtomKey / toRealAtom", () => {
  const columnAtom = {
    kind: "column",
    name: "a",
    type: "Float",
    dtype: "float64",
  };
  const groupAtom = {
    kind: "group",
    converterId: "conv_0",
    slot: 0,
    label: "output",
    converterName: "StandardScaler",
    type: "Float",
  };
  const realColumnAtom = { kind: "column", name: "a" };
  const realGroupAtom = { kind: "group", converter_id: "conv_0", slot: 0 };

  it("keys a column atom by its own name", () => {
    expect(atomKey(columnAtom)).toBe("a");
  });

  it("keys a group atom by the __group__ convention", () => {
    expect(atomKey(groupAtom)).toBe("__group__conv_0__0");
  });

  it("realAtomKey produces the same key as atomKey for the same group", () => {
    expect(realAtomKey(realGroupAtom)).toBe(atomKey(groupAtom));
    expect(realAtomKey(realColumnAtom)).toBe(atomKey(columnAtom));
  });

  it("toRealAtom translates a column atom back to its real shape", () => {
    expect(toRealAtom(columnAtom)).toEqual({ kind: "column", name: "a" });
  });

  it("toRealAtom translates a group atom back to its real (converter_id) shape", () => {
    expect(toRealAtom(groupAtom)).toEqual({
      kind: "group",
      converter_id: "conv_0",
      slot: 0,
    });
  });
});

describe("reseedColumnSelection", () => {
  it("with no previous selection, seeds all-but-last column as input and the last column as output when there are no group atoms", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: {
        a: { type: "Float", dtype: "float64" },
        b: { type: "Float", dtype: "float64" },
        c: { type: "Float", dtype: "float64" },
      },
      converters: [],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: [],
      previousOutputKeys: [],
    });
    expect(result.inputKeys).toEqual(["a", "b"]);
    expect(result.outputKeys).toEqual(["c"]);
  });

  it("prefers the last COLUMN atom as the default output, not a trailing group atom", () => {
    // Regression test: buildAtomList sorts group atoms after every raw
    // dataset column, so a naive "pick the literal last atom" heuristic
    // would default the output selection to a converter's generated
    // feature instead of a real dataset column — essentially never what
    // anyone wants.
    const atoms = buildAtomList({
      datasetColumnTypes: {
        a: { type: "Float", dtype: "float64" },
        b: { type: "Categorical", dtype: "object" },
      },
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "scaled" }] },
        },
      ],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: [],
      previousOutputKeys: [],
    });
    expect(result.outputKeys).toEqual(["b"]);
    expect(result.inputKeys).toEqual(
      expect.arrayContaining(["a", "__group__conv_0__0"]),
    );
    expect(result.inputKeys).not.toContain("b");
  });

  it("falls back to the literal last atom as output when there are no column atoms at all", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: {},
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "scaled" }] },
        },
      ],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: [],
      previousOutputKeys: [],
    });
    expect(result.outputKeys).toEqual(["__group__conv_0__0"]);
    expect(result.inputKeys).toEqual([]);
  });

  it("prunes a previous selection referencing an atom that no longer exists", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: { a: { type: "Float", dtype: "float64" } },
      converters: [],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: ["a", "removed_column"],
      previousOutputKeys: ["also_removed"],
    });
    // Output side was emptied by pruning, so it gets re-seeded — but there's
    // nothing left to pick that "a" (still a valid input) doesn't already
    // hold, so the result is an empty output rather than an overlapping one.
    expect(result.inputKeys).toEqual(["a"]);
    expect(result.outputKeys).toEqual([]);
  });

  it("keeps a still-valid previous selection untouched", () => {
    const atoms = buildAtomList({
      datasetColumnTypes: {
        a: { type: "Float", dtype: "float64" },
        b: { type: "Float", dtype: "float64" },
      },
      converters: [],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: ["a"],
      previousOutputKeys: ["b"],
    });
    expect(result.inputKeys).toEqual(["a"]);
    expect(result.outputKeys).toEqual(["b"]);
  });

  it("adds a converter's group atom to input even when a previous selection already exists", () => {
    // Regression test: a converter configured AFTER the first visit to this
    // step (user already has a saved input/output selection from an earlier
    // visit) must have its group atom default into Input Columns just like
    // a converter configured BEFORE the first visit does — not silently
    // left out as an unselected option only in this ordering.
    const atoms = buildAtomList({
      datasetColumnTypes: {
        a: { type: "Float", dtype: "float64" },
        b: { type: "Float", dtype: "float64" },
      },
      converters: [
        {
          id: "conv_0",
          converter: "StandardScaler",
          metadata: { output_slots: [{ slot: 0, label: "scaled" }] },
        },
      ],
    });
    const result = reseedColumnSelection({
      atoms,
      previousInputKeys: ["a"],
      previousOutputKeys: ["b"],
    });
    expect(result.inputKeys).toEqual(["a", "__group__conv_0__0"]);
    expect(result.outputKeys).toEqual(["b"]);
  });
});

describe("isAtomSelectionValidLocally", () => {
  const taskRequirements = {
    metadata: {
      inputs_types: ["Float", "Integer", "Categorical"],
      inputs_cardinality: "n",
      outputs_types: ["Categorical"],
      outputs_cardinality: 1,
    },
  };

  it("does not treat a null/unknown atom type as a type mismatch on its own", () => {
    // Regression test: several converters (e.g. OneHotEncoder,
    // OrdinalEncoder) don't declare a static output type for a slot, so
    // that atom's `type` is null — this must not, by itself, fail the
    // type check (the real check happens later, at preprocessing/training
    // time via the backend's `prepare_for_task`).
    const result = isAtomSelectionValidLocally({
      inputAtoms: [{ kind: "column", name: "a", type: "Float" }],
      outputAtoms: [
        {
          kind: "group",
          converter_id: "conv_0",
          slot: 0,
          type: null,
        },
      ],
      taskRequirements,
    });
    expect(result).toBe(true);
  });

  it("is NOT valid when taskRequirements hasn't loaded yet (null)", () => {
    // Regression test: previously an empty types list / undefined
    // cardinality both trivially passed, so a null `taskRequirements`
    // (loading race, or a fetch that never recovered) read as
    // permissively valid instead of "not yet known".
    const result = isAtomSelectionValidLocally({
      inputAtoms: [{ kind: "column", name: "a", type: "Float" }],
      outputAtoms: [
        { kind: "group", converter_id: "conv_0", slot: 0, type: null },
      ],
      taskRequirements: null,
    });
    expect(result).toBe(false);
  });

  it("still rejects a genuinely incompatible declared type", () => {
    // Sanity check that the null-type carve-out doesn't neuter the check
    // entirely: a group atom that DOES declare an incompatible type is
    // still rejected.
    const result = isAtomSelectionValidLocally({
      inputAtoms: [{ kind: "column", name: "a", type: "Float" }],
      outputAtoms: [
        {
          kind: "group",
          converter_id: "conv_0",
          slot: 0,
          type: "Text",
        },
      ],
      taskRequirements,
    });
    expect(result).toBe(false);
  });
});
