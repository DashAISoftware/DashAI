import React from "react";
import { screen, fireEvent, waitFor, render } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import ImportSessionButton from "./ImportSessionButton";
import { importModelSession } from "../../api/modelSession";
import { downloadComponent } from "../../api/component";
import { useSnackbar } from "notistack";

jest.mock("notistack", () => {
  const snackbar = { enqueueSnackbar: jest.fn(), closeSnackbar: jest.fn() };
  return { useSnackbar: () => snackbar };
});

jest.mock("../../api/modelSession", () => ({
  importModelSession: jest.fn(),
}));

jest.mock("../../api/component", () => ({
  downloadComponent: jest.fn(() => Promise.resolve({ id: "job-1" })),
  getComponentDownloadStatus: jest.fn(),
  deleteComponentDownload: jest.fn(),
}));

jest.mock("../../utils/jobPoller", () => ({
  startJobPolling: jest.fn(),
  stopJobPolling: jest.fn(),
}));

const m2m = {
  name: "M2M100Transformer",
  display_name: "Transformer Multilingüe M2M-100",
};
const nllb = { name: "NLLBTransformer", display_name: "Transformer NLLB" };

const importFile = async (result) => {
  importModelSession.mockResolvedValue({
    session_id: 7,
    dataset_id: 3,
    session_name: "Translation",
    dataset_name: "languages",
    renamed: { session: false, dataset: false },
    warnings: [],
    recipe_runs: [],
    needs_download_trained: [],
    needs_download_untrained: [],
    ...result,
  });
  const { container } = renderWithProviders(<ImportSessionButton />);
  const input = container.querySelector('input[type="file"]');
  fireEvent.change(input, {
    target: { files: [new File(["zip"], "s.dashai")] },
  });
  const { enqueueSnackbar } = useSnackbar();
  await waitFor(() => expect(enqueueSnackbar).toHaveBeenCalled());
  return enqueueSnackbar.mock.calls;
};

beforeEach(() => jest.clearAllMocks());

test("trained models that need a download only get a notice", async () => {
  const calls = await importFile({ needs_download_trained: [m2m] });

  const notice = calls.find(([message]) => message.includes(m2m.display_name));
  expect(notice[1].variant).toBe("info");
  expect(notice[1].action).toBeUndefined();
});

test("untrained models that need a download offer to download them", async () => {
  const calls = await importFile({ needs_download_untrained: [m2m, nllb] });

  const notice = calls.find(([message]) => message.includes(nllb.display_name));
  expect(notice[1].variant).toBe("warning");
  expect(notice[1].persist).toBe(true);

  render(notice[1].action("key-1"));
  fireEvent.click(screen.getByRole("button", { name: /download/i }));

  await waitFor(() => expect(downloadComponent).toHaveBeenCalledTimes(2));
  expect(downloadComponent).toHaveBeenCalledWith("M2M100Transformer");
  expect(downloadComponent).toHaveBeenCalledWith("NLLBTransformer");
});
