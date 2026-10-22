import React from "react";
import { screen, fireEvent, waitFor } from "@testing-library/react";
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
};

beforeEach(() => jest.clearAllMocks());

test("an import with nothing to report only shows a success snackbar", async () => {
  await importFile({});

  const { enqueueSnackbar } = useSnackbar();
  await waitFor(() => expect(enqueueSnackbar).toHaveBeenCalled());
  expect(enqueueSnackbar.mock.calls[0][1].variant).toBe("success");
  expect(screen.queryByRole("button", { name: /got it/i })).toBeNull();
});

test("download notices stay in the modal until dismissed", async () => {
  await importFile({ needs_download_trained: [m2m] });

  expect(
    await screen.findByText(new RegExp(m2m.display_name)),
  ).toBeInTheDocument();
  expect(useSnackbar().enqueueSnackbar).not.toHaveBeenCalled();

  fireEvent.click(screen.getByRole("button", { name: /got it/i }));
  await waitFor(() =>
    expect(screen.queryByText(new RegExp(m2m.display_name))).toBeNull(),
  );
});

test("untrained models that need a download offer to download them", async () => {
  await importFile({ needs_download_untrained: [m2m, nllb] });

  await screen.findByText(new RegExp(nllb.display_name));
  fireEvent.click(screen.getByRole("button", { name: /^download$/i }));

  await waitFor(() => expect(downloadComponent).toHaveBeenCalledTimes(2));
  expect(downloadComponent).toHaveBeenCalledWith("M2M100Transformer");
  expect(downloadComponent).toHaveBeenCalledWith("NLLBTransformer");
});
