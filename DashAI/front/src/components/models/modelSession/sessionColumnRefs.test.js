import {
  groupKey,
  isGroupKey,
  stepFromGroupKey,
  refToKey,
  keyToRef,
  buildColumnKeysAndTypes,
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

  it("recognizes group keys and extracts their step", () => {
    expect(isGroupKey(groupKey(3))).toBe(true);
    expect(isGroupKey("age")).toBe(false);
    expect(stepFromGroupKey(groupKey(3))).toBe(3);
  });

  it("builds keys/types/labels for raw columns plus every prior step", () => {
    const { allKeys, columnTypes, optionLabels } = buildColumnKeysAndTypes({
      datasetTypes: { age: { type: "Integer" }, text: { type: "Text" } },
      preprocessing: [
        {
          converter: "BagOfWordsConverter",
          outputType: "Integer",
          outputDtype: "int64",
        },
        { converter: "Binarizer", outputType: "Integer" },
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
        { converter: "BagOfWordsConverter", outputType: "Integer" },
        { converter: "Binarizer", outputType: "Integer" },
      ],
    });

    expect(allKeys).toEqual(["age", "__group__0", "__group__1"]);
  });
});
