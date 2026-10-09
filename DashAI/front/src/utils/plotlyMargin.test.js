import { buildPlotMargin } from "./plotlyMargin";

describe("buildPlotMargin", () => {
  it("uses the compact margin in minimalist mode", () => {
    expect(buildPlotMargin({ data: [], layout: {} }, true)).toEqual({
      l: 40,
      r: 20,
      t: 30,
      b: 40,
    });
  });

  it("uses the standard top margin for a cartesian figure with a title", () => {
    const plotData = {
      data: [{ type: "scatter" }],
      layout: { title: { text: "My plot" } },
    };

    expect(buildPlotMargin(plotData, false)).toEqual({
      l: 60,
      r: 30,
      t: 50,
      b: 60,
    });
  });

  it("adds top clearance for a titled parallel coordinates figure", () => {
    // parcoords draws its dimension labels along the top of the plot domain,
    // where the title also sits; the title needs extra room to clear them.
    const plotData = {
      data: [{ type: "parcoords" }],
      layout: { title: { text: "Correlations" } },
    };

    expect(buildPlotMargin(plotData, false).t).toBeGreaterThan(50);
  });

  it("adds top clearance for a titled parallel categories figure", () => {
    const plotData = {
      data: [{ type: "parcats" }],
      layout: { title: "Flows" },
    };

    expect(buildPlotMargin(plotData, false).t).toBeGreaterThan(50);
  });

  it("keeps the standard top margin for parcoords without a title", () => {
    const plotData = { data: [{ type: "parcoords" }], layout: {} };

    expect(buildPlotMargin(plotData, false).t).toBe(50);
  });

  it("ignores an empty title string", () => {
    const plotData = {
      data: [{ type: "parcoords" }],
      layout: { title: "   " },
    };

    expect(buildPlotMargin(plotData, false).t).toBe(50);
  });

  it("survives missing data or layout", () => {
    expect(buildPlotMargin({}, false)).toEqual({ l: 60, r: 30, t: 50, b: 60 });
    expect(buildPlotMargin(undefined, false).t).toBe(50);
  });
});
