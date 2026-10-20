import { formatStructureMessage } from "./structureMessages";

describe("formatStructureMessage", () => {
  it("joins list params so a message can name several columns", () => {
    const t = jest.fn((key, params) => `${key}:${params.columns}`);

    const text = formatStructureMessage(t, {
      code: "drops_columns",
      params: { columns: ["city", "date"] },
    });

    expect(text).toBe("models:structure.drops_columns:city, date");
  });
});
