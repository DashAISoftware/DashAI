import {
  atomColumnName,
  atomColumnNames,
  atomIdentityKey,
  atomListIncludes,
  formatColumnAtom,
  formatColumnList,
  isSameAtom,
} from "./columnAtoms";

const columnAtom = { kind: "column", name: "SepalLengthCm" };
const groupAtom = { kind: "group", converter_id: "conv_0", slot: 0 };

const converters = [
  { id: "conv_0", converter: "BagOfWords" },
  { id: "conv_1", converter: "PCA" },
];

const converterTools = [
  {
    name: "BagOfWords",
    display_name: "Bag of Words",
    metadata: { output_slots: [{ slot: 0, label: "vocabulary" }] },
  },
  { name: "PCA", display_name: "Principal Component Analysis", metadata: {} },
];

describe("atomColumnName / atomColumnNames", () => {
  it("returns the name of a column atom", () => {
    expect(atomColumnName(columnAtom)).toBe("SepalLengthCm");
  });

  it("passes a legacy plain string through unchanged", () => {
    expect(atomColumnName("SepalLengthCm")).toBe("SepalLengthCm");
  });

  it("returns null for a group atom (no raw column name exists yet)", () => {
    expect(atomColumnName(groupAtom)).toBeNull();
  });

  it("returns null for null/undefined", () => {
    expect(atomColumnName(null)).toBeNull();
    expect(atomColumnName(undefined)).toBeNull();
  });

  it("drops group atoms when listing real column names", () => {
    expect(atomColumnNames([columnAtom, groupAtom, "Species"])).toEqual([
      "SepalLengthCm",
      "Species",
    ]);
    expect(atomColumnNames(undefined)).toEqual([]);
  });
});

describe("atomIdentityKey / isSameAtom / atomListIncludes", () => {
  it("keys a column atom by its name and a group atom by converter+slot", () => {
    expect(atomIdentityKey(columnAtom)).toBe("SepalLengthCm");
    expect(atomIdentityKey(groupAtom)).toBe("__group__conv_0__0");
  });

  it("matches a column atom against its legacy plain-string form", () => {
    expect(isSameAtom(columnAtom, "SepalLengthCm")).toBe(true);
    expect(isSameAtom("SepalLengthCm", columnAtom)).toBe(true);
  });

  it("does not match a group atom against a raw column name", () => {
    expect(isSameAtom(groupAtom, "SepalLengthCm")).toBe(false);
  });

  it("matches two structurally equal group atoms", () => {
    expect(
      isSameAtom(groupAtom, { kind: "group", converter_id: "conv_0", slot: 0 }),
    ).toBe(true);
    expect(
      isSameAtom(groupAtom, { kind: "group", converter_id: "conv_1", slot: 0 }),
    ).toBe(false);
  });

  it("never matches un-identifiable values", () => {
    expect(isSameAtom(null, null)).toBe(false);
    expect(isSameAtom({ kind: "mystery" }, { kind: "mystery" })).toBe(false);
  });

  it("replaces a broken `.includes()` membership check", () => {
    const outputColumns = [columnAtom];
    // The defect this exists to prevent: a raw `.includes()` compares an
    // atom object against a plain column name and never matches.
    expect(outputColumns.includes("SepalLengthCm")).toBe(false);
    expect(atomListIncludes(outputColumns, "SepalLengthCm")).toBe(true);
    expect(atomListIncludes(outputColumns, "Species")).toBe(false);
  });
});

describe("formatColumnAtom / formatColumnList", () => {
  it("formats a column atom as its own name", () => {
    expect(formatColumnAtom(columnAtom)).toBe("SepalLengthCm");
  });

  it("formats a legacy plain string as itself", () => {
    expect(formatColumnAtom("Species")).toBe("Species");
  });

  it("formats a group atom as 'ConverterName: slot label'", () => {
    expect(formatColumnAtom(groupAtom, { converters, converterTools })).toBe(
      "Bag of Words: vocabulary",
    );
  });

  it("falls back to the raw converter name and slot number without tools", () => {
    expect(formatColumnAtom(groupAtom, { converters })).toBe("BagOfWords: 0");
  });

  it("returns the unknown label when the source converter is gone", () => {
    expect(
      formatColumnAtom(groupAtom, { converters: [], unknownLabel: "Unknown" }),
    ).toBe("Unknown");
    expect(formatColumnAtom(null, { unknownLabel: "Unknown" })).toBe("Unknown");
  });

  it("always returns a string, never an object (the <Chip> crash site)", () => {
    [columnAtom, groupAtom, "Species", null, { kind: "mystery" }].forEach(
      (atom) => {
        expect(typeof formatColumnAtom(atom, { converters })).toBe("string");
      },
    );
  });

  it("joins a whole list for inline display", () => {
    expect(
      formatColumnList([columnAtom, groupAtom], { converters, converterTools }),
    ).toBe("SepalLengthCm, Bag of Words: vocabulary");
  });
});
