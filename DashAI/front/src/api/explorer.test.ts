jest.mock("./api");

import api from "./api";
import { resetExplorerResults, updateExplorerResults } from "./explorer";

describe("explorer plot override api", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("puts the artifact index alongside the edited figure", async () => {
    (api.put as jest.Mock).mockResolvedValue({ data: { message: "ok" } });
    const figure = { data: [], layout: { title: "edited" } };

    const result = await updateExplorerResults(7, 2, figure);

    expect(api.put).toHaveBeenCalledWith("/v1/explorer/7/results/", {
      index: 2,
      figure,
    });
    expect(result).toEqual({ message: "ok" });
  });

  it("deletes the override for one artifact index", async () => {
    (api.delete as jest.Mock).mockResolvedValue({ data: { message: "ok" } });

    const result = await resetExplorerResults(7, 2);

    expect(api.delete).toHaveBeenCalledWith(
      "/v1/explorer/7/results/override/2",
    );
    expect(result).toEqual({ message: "ok" });
  });
});
