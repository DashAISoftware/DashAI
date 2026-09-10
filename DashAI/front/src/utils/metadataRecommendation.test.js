import {
  META_THRESHOLDS,
  estimateTotalRows,
  shouldRecommendDisableMetadata,
} from "./metadataRecommendation";

describe("estimateTotalRows", () => {
  it("returns 0 when previewRowCount is missing", () => {
    expect(estimateTotalRows({ previewRowCount: 0 })).toBe(0);
    expect(estimateTotalRows({})).toBe(0);
  });

  it("returns previewRowCount when file size is unknown", () => {
    expect(
      estimateTotalRows({ previewRowCount: 100, previewedBytes: 1000 }),
    ).toBe(100);
  });

  it("scales by fileSize / previewedBytes when both known", () => {
    expect(
      estimateTotalRows({
        previewRowCount: 100,
        previewedBytes: 1000,
        fileSize: 10000,
      }),
    ).toBe(1000);
  });

  it("rounds the estimate", () => {
    expect(
      estimateTotalRows({
        previewRowCount: 7,
        previewedBytes: 1000,
        fileSize: 1333,
      }),
    ).toBe(9);
  });
});

describe("shouldRecommendDisableMetadata", () => {
  it("recommends disable when columns exceed threshold", () => {
    expect(
      shouldRecommendDisableMetadata({
        colCount: META_THRESHOLDS.COLS + 1,
        estRows: 100,
      }),
    ).toBe(true);
  });

  it("recommends disable when rows exceed threshold", () => {
    expect(
      shouldRecommendDisableMetadata({
        colCount: 5,
        estRows: META_THRESHOLDS.ROWS + 1,
      }),
    ).toBe(true);
  });

  it("does not recommend disable below both thresholds", () => {
    expect(shouldRecommendDisableMetadata({ colCount: 5, estRows: 100 })).toBe(
      false,
    );
  });

  it("ignores estRows when 0 / falsy", () => {
    expect(shouldRecommendDisableMetadata({ colCount: 5, estRows: 0 })).toBe(
      false,
    );
  });
});
