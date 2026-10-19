import { act, renderHook } from "@testing-library/react";
import usePreprocessingStructure from "./usePreprocessingStructure";
import { getPreprocessingStructure } from "../../../api/modelSession";

jest.mock("../../../api/modelSession", () => ({
  getPreprocessingStructure: jest.fn(),
}));

const deferred = () => {
  let resolve;
  const promise = new Promise((done) => {
    resolve = done;
  });
  return { promise, resolve };
};

const args = (steps) => ({
  datasetId: 1,
  candidates: ["age"],
  outputColumns: ["label"],
  steps,
});

describe("usePreprocessingStructure", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    getPreprocessingStructure.mockReset();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("sends one request for quick successive edits", async () => {
    getPreprocessingStructure.mockResolvedValue({ valid: true });
    const { rerender } = renderHook(
      (props) => usePreprocessingStructure(props),
      {
        initialProps: args([]),
      },
    );

    rerender(args([{ converter: "PCA", params: {}, scope: [] }]));
    await act(async () => {
      jest.advanceTimersByTime(300);
    });

    expect(getPreprocessingStructure).toHaveBeenCalledTimes(1);
    expect(getPreprocessingStructure.mock.calls[0][0].steps).toHaveLength(1);
  });

  it("never lets a slower, older response overwrite a newer one", async () => {
    const older = deferred();
    const newer = deferred();
    getPreprocessingStructure
      .mockReturnValueOnce(older.promise)
      .mockReturnValueOnce(newer.promise);
    const { result, rerender } = renderHook(
      (props) => usePreprocessingStructure(props),
      { initialProps: args([]) },
    );

    await act(async () => {
      jest.advanceTimersByTime(300);
    });
    rerender(args([{ converter: "PCA", params: {}, scope: [] }]));
    await act(async () => {
      jest.advanceTimersByTime(300);
    });
    await act(async () => {
      newer.resolve({ id: "newer" });
    });
    await act(async () => {
      older.resolve({ id: "older" });
    });

    expect(result.current.structure).toEqual({ id: "newer" });
    expect(result.current.loading).toBe(false);
  });
});
