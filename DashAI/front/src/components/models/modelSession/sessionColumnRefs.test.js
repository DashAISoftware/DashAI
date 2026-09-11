import {
  groupKey,
  isGroupKey,
  stepFromGroupKey,
  slotFromGroupKey,
  refToKey,
  keyToRef,
  buildColumnKeysAndTypes,
  buildStepDisplayNames,
  resolveDeclaredOutputSlots,
  rawColumnsNeededFor,
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

  it("builds keys/types/labels for raw columns plus every prior step", () => {
    const { allKeys, columnTypes, optionLabels } = buildColumnKeysAndTypes({
      datasetTypes: { age: { type: "Integer" }, text: { type: "Text" } },
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
        {
          converter: "Binarizer",
          outputSlots: [{ slot: null, type: "Integer", dtype: null }],
        },
      ],
      uptoStep: 1,
    });

    expect(allKeys).toEqual(["age", "text", "__group__0"]);
    expect(columnTypes.__group__0).toEqual({ type: "Integer", dtype: "int64" });
    expect(optionLabels.__group__0).toBe("BagOfWordsConverter: output");
    // step 1 (Binarizer) is excluded: uptoStep=1 only includes steps before it
    expect(allKeys).not.toContain(groupKey(1));
  });

  it("includes every step when uptoStep is omitted", () => {
    const { allKeys } = buildColumnKeysAndTypes({
      datasetTypes: { age: { type: "Integer" } },
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          outputSlots: [{ slot: null, type: "Integer" }],
        },
        {
          converter: "Binarizer",
          outputSlots: [{ slot: null, type: "Integer" }],
        },
      ],
    });

    expect(allKeys).toEqual(["age", "__group__0", "__group__1"]);
  });

  it("offers one key per declared slot for a step with a heterogeneous scope", () => {
    const { allKeys, columnTypes, optionLabels } = buildColumnKeysAndTypes({
      datasetTypes: {},
      preprocessing: [
        {
          converter: "SimpleImputer",
          outputSlots: [
            { slot: "Integer", type: "Integer", dtype: "int64" },
            { slot: "Categorical", type: "Categorical", dtype: null },
          ],
        },
      ],
    });

    const integerKey = groupKey(0, "Integer");
    const categoricalKey = groupKey(0, "Categorical");
    expect(allKeys).toEqual([integerKey, categoricalKey]);
    expect(columnTypes[integerKey]).toEqual({
      type: "Integer",
      dtype: "int64",
    });
    expect(columnTypes[categoricalKey]).toEqual({
      type: "Categorical",
      dtype: null,
    });
    expect(optionLabels[integerKey]).toBe("SimpleImputer: output (Integer)");
    expect(optionLabels[categoricalKey]).toBe(
      "SimpleImputer: output (Categorical)",
    );
  });

  it("disambiguates option labels for two steps of the same converter type", () => {
    const { optionLabels } = buildColumnKeysAndTypes({
      datasetTypes: {},
      preprocessing: [
        {
          converter: "SimpleImputer",
          outputSlots: [{ slot: null, type: "Float" }],
        },
        {
          converter: "SimpleImputer",
          outputSlots: [{ slot: null, type: "Float" }],
        },
      ],
      convertersMeta: {
        SimpleImputer: { display_name: "Simple Imputer" },
      },
    });

    expect(optionLabels[groupKey(0)]).toBe("Simple Imputer: output");
    expect(optionLabels[groupKey(1)]).toBe("Simple Imputer (2): output");
  });

  it("falls back to a single unslotted key for a step predating outputSlots", () => {
    const { allKeys, columnTypes } = buildColumnKeysAndTypes({
      datasetTypes: {},
      preprocessing: [
        { converter: "Binarizer", outputType: "Integer", outputDtype: "int64" },
      ],
    });

    expect(allKeys).toEqual(["__group__0"]);
    expect(columnTypes.__group__0).toEqual({ type: "Integer", dtype: "int64" });
  });

  describe("resolveDeclaredOutputSlots", () => {
    const datasetTypes = {
      age: { type: "Integer", dtype: "int64" },
      score: { type: "Float", dtype: "float64" },
      name: { type: "Text", dtype: "string" },
    };

    it("falls back to the converter's declared metadata by default", () => {
      const tool = {
        name: "Binarizer",
        metadata: { output_type: "Integer", output_dtype: "int64" },
      };
      const result = resolveDeclaredOutputSlots({
        tool,
        params: {},
        scope: [{ kind: "raw", name: "age" }],
        datasetTypes,
        preprocessing: [],
      });
      expect(result).toEqual([{ slot: null, type: "Integer", dtype: "int64" }]);
    });

    it("uses the scope's real type when the converter preserves input type", () => {
      const tool = {
        name: "SelectKBest",
        metadata: { output_type: "Float", preserves_input_type: true },
      };
      const result = resolveDeclaredOutputSlots({
        tool,
        params: {},
        scope: [{ kind: "raw", name: "age" }],
        datasetTypes,
        preprocessing: [],
      });
      expect(result).toEqual([{ slot: null, type: "Integer", dtype: "int64" }]);
    });

    it("splits into one slot per distinct type when a preserving converter's scope mixes types", () => {
      const tool = {
        name: "VarianceThreshold",
        metadata: { output_type: "Float", preserves_input_type: true },
      };
      const result = resolveDeclaredOutputSlots({
        tool,
        params: {},
        scope: [
          { kind: "raw", name: "age" },
          { kind: "raw", name: "name" },
        ],
        datasetTypes,
        preprocessing: [],
      });
      expect(result).toEqual(
        expect.arrayContaining([
          { slot: "Integer", type: "Integer", dtype: "int64" },
          { slot: "Text", type: "Text", dtype: "string" },
        ]),
      );
      expect(result).toHaveLength(2);
    });

    it("treats SimpleImputer as type-preserving only for most_frequent/constant", () => {
      const tool = {
        name: "SimpleImputer",
        metadata: { output_type: "Float", output_dtype: null },
      };
      const scope = [{ kind: "raw", name: "name" }];

      const mostFrequent = resolveDeclaredOutputSlots({
        tool,
        params: { strategy: "most_frequent" },
        scope,
        datasetTypes,
        preprocessing: [],
      });
      expect(mostFrequent).toEqual([
        { slot: null, type: "Text", dtype: "string" },
      ]);

      const mean = resolveDeclaredOutputSlots({
        tool,
        params: { strategy: "mean" },
        scope,
        datasetTypes,
        preprocessing: [],
      });
      expect(mean).toEqual([{ slot: null, type: "Float", dtype: null }]);
    });

    it("resolves a preserving converter's scope through a chained group ref", () => {
      const tool = {
        name: "SelectKBest",
        metadata: { output_type: "Float", preserves_input_type: true },
      };
      const preprocessing = [
        {
          converter: "BagOfWordsConverter",
          outputSlots: [{ slot: null, type: "Integer", dtype: "int64" }],
        },
      ];
      const result = resolveDeclaredOutputSlots({
        tool,
        params: {},
        scope: [{ kind: "group", step: 0 }],
        datasetTypes,
        preprocessing,
      });
      expect(result).toEqual([{ slot: null, type: "Integer", dtype: "int64" }]);
    });

    it("resolves a preserving converter's scope through one specific slot of a chained group ref", () => {
      const tool = {
        name: "SelectKBest",
        metadata: { output_type: "Float", preserves_input_type: true },
      };
      const preprocessing = [
        {
          converter: "SimpleImputer",
          outputSlots: [
            { slot: "Integer", type: "Integer", dtype: "int64" },
            { slot: "Categorical", type: "Categorical", dtype: null },
          ],
        },
      ];
      const result = resolveDeclaredOutputSlots({
        tool,
        params: {},
        scope: [{ kind: "group", step: 0, slot: "Integer" }],
        datasetTypes,
        preprocessing,
      });
      expect(result).toEqual([{ slot: null, type: "Integer", dtype: "int64" }]);
    });
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
});
