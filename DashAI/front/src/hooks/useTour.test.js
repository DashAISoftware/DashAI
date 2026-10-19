import { renderHook, act } from "@testing-library/react";
import { useTour } from "./useTour";
import { getToursAutostart } from "../api/appConfig";

jest.mock("../api/appConfig", () => ({ getToursAutostart: jest.fn() }));

// Pass the 500 ms delay, then let the mocked getToursAutostart promise settle.
const settleAutostart = async () => {
  act(() => {
    jest.advanceTimersByTime(600);
  });
  await act(async () => {
    await Promise.resolve();
  });
};

describe("useTour auto-start", () => {
  beforeEach(() => {
    jest.useFakeTimers();
    localStorage.clear();
  });

  afterEach(() => {
    jest.useRealTimers();
  });

  it("opens an unseen tour when auto-start is enabled", async () => {
    getToursAutostart.mockResolvedValue(true);
    const { result } = renderHook(() => useTour("hub"));
    await settleAutostart();
    expect(result.current.run).toBe(true);
  });

  it("stays closed when tours are disabled app-wide", async () => {
    getToursAutostart.mockResolvedValue(false);
    const { result } = renderHook(() => useTour("hub"));
    await settleAutostart();
    expect(result.current.run).toBe(false);
  });

  it("can still be started manually when auto-start is disabled", async () => {
    getToursAutostart.mockResolvedValue(false);
    const { result } = renderHook(() => useTour("hub"));
    await settleAutostart();
    act(() => result.current.startTour());
    expect(result.current.run).toBe(true);
  });

  it("stays closed for a tour already completed", async () => {
    localStorage.setItem(
      "dashai_tours_completed",
      JSON.stringify({ hub: true }),
    );
    getToursAutostart.mockResolvedValue(true);
    const { result } = renderHook(() => useTour("hub"));
    await settleAutostart();
    expect(result.current.run).toBe(false);
    expect(getToursAutostart).not.toHaveBeenCalled();
  });
});
