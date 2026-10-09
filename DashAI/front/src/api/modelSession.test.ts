jest.mock("./api");

import api from "./api";
import { createModelSession } from "./modelSession";

describe("createModelSession", () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (api.post as jest.Mock).mockResolvedValue({ data: { id: "session-1" } });
  });

  it("includes preprocessing and input_column_refs in the request body", async () => {
    await createModelSession(
      1,
      "TabularClassificationTask",
      "session-1",
      [],
      ["label"],
      [],
      [],
      [],
      "holdout",
      JSON.parse("{}"),
      [
        {
          converter: "Binarizer",
          params: { threshold: 0.5 },
          scope: [{ kind: "raw", name: "age" }],
        },
      ],
      [{ kind: "group", step: 0 }],
    );

    expect(api.post).toHaveBeenCalledWith(
      "/v1/model-session/",
      expect.objectContaining({
        preprocessing: [
          {
            converter: "Binarizer",
            params: { threshold: 0.5 },
            scope: [{ kind: "raw", name: "age" }],
          },
        ],
        input_column_refs: [{ kind: "group", step: 0 }],
      }),
    );
  });

  it("defaults preprocessing and input_column_refs to empty arrays", async () => {
    await createModelSession(
      1,
      "TabularClassificationTask",
      "session-2",
      ["age"],
      ["label"],
      [],
      [],
      [],
      "holdout",
      JSON.parse("{}"),
    );

    expect(api.post).toHaveBeenCalledWith(
      "/v1/model-session/",
      expect.objectContaining({ preprocessing: [], input_column_refs: [] }),
    );
  });
});
