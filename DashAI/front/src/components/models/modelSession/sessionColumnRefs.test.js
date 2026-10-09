import {
  groupKey,
  isGroupKey,
  stepFromGroupKey,
  slotFromGroupKey,
  refToKey,
  keyToRef,
  buildStepDisplayNames,
  rawColumnsNeededFor,
  itemToRef,
  stateToOptions,
  labelForRef,
} from "./sessionColumnRefs";

describe("sessionColumnRefs", () => {
  it("round-trips a raw ColumnRef through a key", () => {
    const ref = { kind: "raw", name: "age" };
    expect(keyToRef(refToKey(ref))).toEqual(ref);
  });

  it("round-trips a group ColumnRef through a key", () => {
    const ref = { kind: "group", step: 2 };
    expect(keyToRef(refToKey(ref))).toEqual(ref);
  });

  it("round-trips a slotted group ColumnRef through a key", () => {
    const ref = { kind: "group", step: 0, slot: "Categorical" };
    expect(keyToRef(refToKey(ref))).toEqual(ref);
  });

  it("recognizes group keys and extracts their step", () => {
    expect(isGroupKey(groupKey(3))).toBe(true);
    expect(isGroupKey("age")).toBe(false);
    expect(stepFromGroupKey(groupKey(3))).toBe(3);
  });

  it("extracts both step and slot from a slotted group key", () => {
    const key = groupKey(2, "Categorical");
    expect(stepFromGroupKey(key)).toBe(2);
    expect(slotFromGroupKey(key)).toBe("Categorical");
    expect(slotFromGroupKey(groupKey(2))).toBeNull();
  });

  describe("buildStepDisplayNames", () => {
    it("leaves a converter type's name unchanged when it appears only once", () => {
      const steps = [
        { converter: "SimpleImputer" },
        { converter: "Binarizer" },
      ];
      const convertersMeta = {
        SimpleImputer: { display_name: "Simple Imputer" },
        Binarizer: { display_name: "Binarizer" },
      };
      expect(buildStepDisplayNames(steps, convertersMeta)).toEqual([
        "Simple Imputer",
        "Binarizer",
      ]);
    });

    it("numbers repeated converter types by order of appearance", () => {
      const steps = [
        { converter: "SimpleImputer" },
        { converter: "Binarizer" },
        { converter: "SimpleImputer" },
        { converter: "SimpleImputer" },
      ];
      const convertersMeta = {
        SimpleImputer: { display_name: "Simple Imputer" },
        Binarizer: { display_name: "Binarizer" },
      };
      expect(buildStepDisplayNames(steps, convertersMeta)).toEqual([
        "Simple Imputer",
        "Binarizer",
        "Simple Imputer (2)",
        "Simple Imputer (3)",
      ]);
    });

    it("falls back to the raw registry name when metadata hasn't loaded, still disambiguating", () => {
      const steps = [
        { converter: "SimpleImputer" },
        { converter: "SimpleImputer" },
      ];
      expect(buildStepDisplayNames(steps, {})).toEqual([
        "SimpleImputer",
        "SimpleImputer (2)",
      ]);
    });
  });

  describe("rawColumnsNeededFor", () => {
    it("returns raw ref names as-is", () => {
      const refs = [
        { kind: "raw", name: "age" },
        { kind: "raw", name: "score" },
      ];
      expect(rawColumnsNeededFor(refs, [])).toEqual(["age", "score"]);
    });

    it("resolves a group ref to its step's own raw scope", () => {
      const refs = [{ kind: "group", step: 0 }];
      const steps = [
        {
          converter: "BagOfWordsConverter",
          scope: [{ kind: "raw", name: "text" }],
        },
      ];
      expect(rawColumnsNeededFor(refs, steps)).toEqual(["text"]);
    });

    it("resolves a chained group ref recursively through an earlier step", () => {
      const refs = [{ kind: "group", step: 1 }];
      const steps = [
        {
          converter: "BagOfWordsConverter",
          scope: [{ kind: "raw", name: "text" }],
        },
        { converter: "PCA", scope: [{ kind: "group", step: 0 }] },
      ];
      expect(rawColumnsNeededFor(refs, steps)).toEqual(["text"]);
    });

    it("ignores slot when walking a group ref back to raw columns", () => {
      const refs = [{ kind: "group", step: 0, slot: "Integer" }];
      const steps = [
        {
          converter: "SimpleImputer",
          scope: [
            { kind: "raw", name: "age" },
            { kind: "raw", name: "city" },
          ],
        },
      ];
      // The slot only narrows which OUTPUT columns you get; fitting the
      // step still needs every raw column in its scope, regardless.
      expect(rawColumnsNeededFor(refs, steps)).toEqual(["age", "city"]);
    });

    it("de-duplicates a raw column needed by more than one ref", () => {
      const refs = [
        { kind: "raw", name: "age" },
        { kind: "group", step: 0 },
      ];
      const steps = [
        { converter: "Doubler", scope: [{ kind: "raw", name: "age" }] },
      ];
      expect(rawColumnsNeededFor(refs, steps)).toEqual(["age"]);
    });

    it("skips a group ref pointing at a step that doesn't exist", () => {
      const refs = [
        { kind: "raw", name: "age" },
        { kind: "group", step: 5 },
      ];
      expect(rawColumnsNeededFor(refs, [])).toEqual(["age"]);
    });
  });

  describe("named group refs", () => {
    it("round-trips a named group ColumnRef through a key", () => {
      const ref = { kind: "group", step: 1, name: "date_month" };
      const key = refToKey(ref);
      expect(isGroupKey(key)).toBe(true);
      expect(stepFromGroupKey(key)).toBe(1);
      expect(slotFromGroupKey(key)).toBeNull();
      expect(keyToRef(key)).toEqual(ref);
    });

    it("keeps a column name containing the separators intact", () => {
      const ref = { kind: "group", step: 0, name: "a__slot__b" };
      expect(keyToRef(refToKey(ref))).toEqual(ref);
    });
  });

  describe("itemToRef", () => {
    it("refs an original column by name", () => {
      const item = { kind: "column", name: "age", origin: null };
      expect(itemToRef(item)).toEqual({ kind: "raw", name: "age" });
    });

    it("refs a generated column by its step and name", () => {
      const item = { kind: "column", name: "date_month", origin: 2 };
      expect(itemToRef(item)).toEqual({
        kind: "group",
        step: 2,
        name: "date_month",
      });
    });

    it("refs a lone block as its step's whole group", () => {
      const item = { kind: "block", step: 0, slot: null };
      expect(itemToRef(item)).toEqual({ kind: "group", step: 0 });
    });

    it("refs one of several blocks by its slot", () => {
      const item = { kind: "block", step: 0, slot: "Float" };
      expect(itemToRef(item)).toEqual({
        kind: "group",
        step: 0,
        slot: "Float",
      });
    });
  });

  describe("stateToOptions", () => {
    const state = [
      {
        kind: "column",
        name: "age",
        type: "Integer",
        dtype: "int64",
        origin: null,
      },
      {
        kind: "column",
        name: "date_month",
        type: "Integer",
        dtype: "int64",
        origin: 1,
      },
      {
        kind: "block",
        step: 0,
        slot: null,
        label: "output",
        type: "Float",
        dtype: "float64",
        count: 2,
      },
      {
        kind: "block",
        step: 2,
        slot: null,
        label: "ohe_*",
        type: "Integer",
        dtype: "int64",
        count: null,
      },
    ];
    const stepNames = ["PCA", "Date Features", "One Hot Encoder"];

    it("keys every item as the ref it stands for, typed", () => {
      const { allKeys, columnTypes } = stateToOptions(state, stepNames);

      expect(allKeys.map(keyToRef)).toEqual(state.map(itemToRef));
      expect(columnTypes.age).toEqual({ type: "Integer", dtype: "int64" });
      expect(columnTypes[allKeys[2]]).toEqual({
        type: "Float",
        dtype: "float64",
      });
    });

    it("labels blocks with their step and size, N when unknown", () => {
      const { allKeys, optionLabels } = stateToOptions(state, stepNames);

      expect(optionLabels[allKeys[0]]).toBeUndefined();
      expect(optionLabels[allKeys[1]]).toBe("date_month");
      expect(optionLabels[allKeys[2]]).toBe("PCA: output (2 columns)");
      expect(optionLabels[allKeys[3]]).toBe(
        "One Hot Encoder: ohe_* (N columns)",
      );
    });

    it("translates block labels, with a singular for one column", () => {
      const spanish = (key, params = {}) =>
        ({
          "models:structure.output": "salida",
          "models:structure.unknownColumns": "N columnas",
          "models:structure.columns":
            params.count === 1 ? "1 columna" : `${params.count} columnas`,
        })[key];

      const { allKeys, optionLabels } = stateToOptions(
        state,
        stepNames,
        spanish,
      );
      const single = stateToOptions(
        [{ ...state[2], count: 1 }],
        stepNames,
        spanish,
      );

      expect(optionLabels[allKeys[2]]).toBe("PCA: salida (2 columnas)");
      expect(optionLabels[allKeys[3]]).toBe(
        "One Hot Encoder: ohe_* (N columnas)",
      );
      expect(single.optionLabels[single.allKeys[0]]).toBe(
        "PCA: salida (1 columna)",
      );
    });
  });

  describe("labelForRef", () => {
    const stepNames = ["PCA", "Date Features"];

    it("labels a ref without needing the estimated structure", () => {
      expect(labelForRef({ kind: "raw", name: "age" }, stepNames)).toBe("age");
      expect(
        labelForRef({ kind: "group", step: 1, name: "date_month" }, stepNames),
      ).toBe("date_month");
      expect(labelForRef({ kind: "group", step: 0 }, stepNames)).toBe(
        "PCA: output",
      );
      expect(
        labelForRef({ kind: "group", step: 0, slot: "Float" }, stepNames),
      ).toBe("PCA: output (Float)");
    });

    it("translates the word output", () => {
      const spanish = (key) => ({ "models:structure.output": "salida" })[key];

      expect(labelForRef({ kind: "group", step: 0 }, stepNames, spanish)).toBe(
        "PCA: salida",
      );
    });
  });
});
