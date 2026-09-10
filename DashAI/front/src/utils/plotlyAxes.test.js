import { buildAxisResetUpdate } from "./plotlyAxes";

describe("buildAxisResetUpdate", () => {
  it("autoranges both axes of a cartesian figure", () => {
    const fullLayout = { xaxis: { range: [0, 1] }, yaxis: { range: [0, 1] } };

    expect(buildAxisResetUpdate(fullLayout)).toEqual({
      "xaxis.autorange": true,
      "yaxis.autorange": true,
    });
  });

  it("returns null for a parallel coordinates figure", () => {
    // parcoords is not cartesian: its computed layout carries no xaxis or
    // yaxis, and asking Plotly to autorange one throws inside relayout.
    const fullLayout = { dragmode: "zoom", margin: {} };

    expect(buildAxisResetUpdate(fullLayout)).toBeNull();
  });

  it("returns null for a polar figure", () => {
    const fullLayout = { polar: { radialaxis: {}, angularaxis: {} } };

    expect(buildAxisResetUpdate(fullLayout)).toBeNull();
  });

  it("autoranges only the axis that exists", () => {
    const fullLayout = { xaxis: { range: [0, 1] } };

    expect(buildAxisResetUpdate(fullLayout)).toEqual({
      "xaxis.autorange": true,
    });
  });

  it("returns null when the layout is missing entirely", () => {
    expect(buildAxisResetUpdate(undefined)).toBeNull();
    expect(buildAxisResetUpdate(null)).toBeNull();
  });
});
