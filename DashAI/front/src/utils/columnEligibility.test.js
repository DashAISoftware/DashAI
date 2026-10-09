/**
 * The metadata contract, asserted from the browser's side.
 *
 * Both halves of this were live defects, and both were silent in different
 * ways: the polarity mistake disabled every unrestricted explorer, and the
 * renamed key threw before the user could see anything at all. Neither would
 * have survived a test of the contract itself, which is what this is.
 *
 * The backend half is pinned in tests/back/test_component_metadata_contract.py.
 */

import { evaluateColumnEligibility, refusedDtypes } from "./columnEligibility";

const COLUMNS = [
  { columnName: "age", dataType: "int64", valueType: "Numerical" },
  { columnName: "price", dataType: "float64", valueType: "Numerical" },
  { columnName: "city", dataType: "string", valueType: "Categorical" },
  { columnName: "active", dataType: "bool", valueType: "Categorical" },
];

const NO_RESTRICTION = {
  allowed_types: [],
  allowed_dtypes: [],
  non_allowed_dtypes: [],
  input_cardinality: { min: 1 },
};

describe("an empty restriction list means no restriction", () => {
  it("accepts every column when nothing is restricted", () => {
    const { validColumns, shortfall, restricted } = evaluateColumnEligibility(
      NO_RESTRICTION,
      COLUMNS,
    );
    // The bug this replaces read an empty allowed_dtypes as "nothing allowed",
    // filtered every column away, and then disabled the explorer for failing
    // its own minimum of one column.
    expect(validColumns).toHaveLength(4);
    expect(shortfall).toBeNull();
    expect(restricted).toBe(false);
  });

  it("does not look for a star, which the backend normalizes away", () => {
    // ["*"] never reaches the browser: base_explorer turns it into []. A
    // frontend that tests for "*" is testing for something it cannot receive.
    const { validColumns } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, allowed_dtypes: [] },
      COLUMNS,
    );
    expect(validColumns).toHaveLength(4);
  });

  it("tolerates metadata that declares nothing at all", () => {
    expect(evaluateColumnEligibility({}, COLUMNS).validColumns).toHaveLength(4);
    expect(
      evaluateColumnEligibility(undefined, COLUMNS).validColumns,
    ).toHaveLength(4);
    expect(evaluateColumnEligibility({}, undefined).validColumns).toEqual([]);
  });
});

describe("the three restrictions", () => {
  it("filters by semantic type", () => {
    const { validColumns, restrictions } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, allowed_types: ["Numerical"] },
      COLUMNS,
    );
    expect(validColumns.map((c) => c.columnName)).toEqual(["age", "price"]);
    expect(restrictions).toEqual(["Numerical"]);
  });

  it("filters by dtype", () => {
    const { validColumns } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, allowed_dtypes: ["int64"] },
      COLUMNS,
    );
    expect(validColumns.map((c) => c.columnName)).toEqual(["age"]);
  });

  it("applies the blacklist, which is what the stale key silently skipped", () => {
    // The seven explorers and two converters that declare one all spell it
    // ["string", "bool", ""].
    const { validColumns, restricted } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, non_allowed_dtypes: ["string", "bool", ""] },
      COLUMNS,
    );
    expect(validColumns.map((c) => c.columnName)).toEqual(["age", "price"]);
    expect(restricted).toBe(true);
  });

  it("matches the backend's empty-string dtype against the unknown label", () => {
    // A column whose dtype the backend could not name is "" in the blacklist
    // and a localized word in the column table, so the two have to be lined up.
    const columns = [
      ...COLUMNS,
      { columnName: "mystery", dataType: "Desconocido", valueType: "Unknown" },
    ];
    const metadata = { ...NO_RESTRICTION, non_allowed_dtypes: [""] };

    const withLabel = evaluateColumnEligibility(metadata, columns, {
      unknownLabel: "Desconocido",
    });
    expect(withLabel.validColumns.map((c) => c.columnName)).not.toContain(
      "mystery",
    );

    // Without the label there is nothing to line up, so the column survives.
    const withoutLabel = evaluateColumnEligibility(metadata, columns);
    expect(withoutLabel.validColumns.map((c) => c.columnName)).toContain(
      "mystery",
    );
  });

  it("applies all three together", () => {
    const { validColumns } = evaluateColumnEligibility(
      {
        ...NO_RESTRICTION,
        allowed_types: ["Numerical", "Categorical"],
        allowed_dtypes: ["int64", "float64", "string"],
        non_allowed_dtypes: ["string"],
      },
      COLUMNS,
    );
    expect(validColumns.map((c) => c.columnName)).toEqual(["age", "price"]);
  });
});

describe("cardinality", () => {
  it("reports a shortfall against an exact requirement", () => {
    const { shortfall } = evaluateColumnEligibility(
      {
        ...NO_RESTRICTION,
        allowed_dtypes: ["int64"],
        input_cardinality: { exact: 2 },
      },
      COLUMNS,
    );
    expect(shortfall).toEqual({ kind: "exact", required: 2, available: 1 });
  });

  it("reports a shortfall against a minimum", () => {
    const { shortfall } = evaluateColumnEligibility(
      {
        ...NO_RESTRICTION,
        allowed_dtypes: ["int64"],
        input_cardinality: { min: 3 },
      },
      COLUMNS,
    );
    expect(shortfall).toEqual({ kind: "min", required: 3, available: 1 });
  });

  it("reports none when the requirement is met", () => {
    const { shortfall } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, input_cardinality: { min: 2 } },
      COLUMNS,
    );
    expect(shortfall).toBeNull();
  });

  it("prefers exact over min when a component declares both", () => {
    const { shortfall } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, input_cardinality: { exact: 1, min: 99 } },
      COLUMNS,
    );
    expect(shortfall).toBeNull();
  });

  it("treats a maximum as no shortfall", () => {
    // A component that accepts at most N columns is never unusable for having
    // too many: the picker just lets the user choose fewer.
    const { shortfall } = evaluateColumnEligibility(
      { ...NO_RESTRICTION, input_cardinality: { min: 1, max: 2 } },
      COLUMNS,
    );
    expect(shortfall).toBeNull();
  });
});

describe("refusedDtypes", () => {
  it("reads the current key", () => {
    expect(refusedDtypes({ non_allowed_dtypes: ["string"] })).toEqual([
      "string",
    ]);
  });

  it("does not resurrect the old one", () => {
    // Reading restricted_dtypes is what made the "does not accept" chips
    // invisible for as long as the key had the old name.
    expect(refusedDtypes({ restricted_dtypes: ["string"] })).toEqual([]);
  });

  it("is empty for metadata without a blacklist", () => {
    expect(refusedDtypes({})).toEqual([]);
    expect(refusedDtypes(undefined)).toEqual([]);
  });
});
