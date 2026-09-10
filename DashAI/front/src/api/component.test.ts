jest.mock("./api");

import api from "./api";
import { downloadComponent } from "./component";

describe("component download api", () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it("posts to the download endpoint and returns the job id", async () => {
    (api.post as jest.Mock).mockResolvedValue({ data: { id: "job-1" } });

    const result = await downloadComponent("OpusMtEnRoaTransformer");
    expect(api.post).toHaveBeenCalledWith(
      "/v1/component/OpusMtEnRoaTransformer/download",
    );
    expect(result).toEqual({ id: "job-1" });
  });
});
