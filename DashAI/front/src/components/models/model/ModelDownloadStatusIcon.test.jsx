import React from "react";
import { screen, fireEvent, waitFor } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";

jest.mock("../../../api/component", () => ({
  downloadComponent: jest.fn(() => Promise.resolve({ id: "job-1" })),
  deleteComponentDownload: jest.fn(() => Promise.resolve()),
  getComponentDownloadStatus: jest.fn(() =>
    Promise.resolve({ downloaded: false, requires_download: true }),
  ),
}));
jest.mock("../../../utils/jobPoller", () => ({
  startJobPolling: jest.fn(),
  stopJobPolling: jest.fn(),
  subscribeJobs: jest.fn(() => () => {}),
}));
jest.mock("../../../api/credentials", () => ({
  getCredentials: jest.fn(() => Promise.resolve([])),
  authenticateCredential: jest.fn(),
  deleteCredential: jest.fn(),
}));

import ModelDownloadStatusIcon from "./ModelDownloadStatusIcon";
import { deleteComponentDownload } from "../../../api/component";

const model = {
  name: "DownloadableTestModel",
  downloaded: false,
  metadata: { requires_download: true, download_size_bytes: 268435456 },
};

describe("ModelDownloadStatusIcon", () => {
  it("renders no interactive control for an undownloaded model", () => {
    renderWithProviders(
      <ModelDownloadStatusIcon model={model} onChanged={() => {}} />,
    );
    expect(screen.queryByRole("button")).toBeNull();
  });

  it("deletes a downloaded model after confirming in the modal", async () => {
    renderWithProviders(
      <ModelDownloadStatusIcon
        model={{ ...model, downloaded: true }}
        onChanged={() => {}}
      />,
    );
    const del = await screen.findByRole("button", { name: "Delete download" });
    fireEvent.click(del);
    // Deletion only happens after confirming in the modal.
    expect(deleteComponentDownload).not.toHaveBeenCalled();
    const confirm = await screen.findByRole("button", { name: "Delete" });
    fireEvent.click(confirm);
    await waitFor(() =>
      expect(deleteComponentDownload).toHaveBeenCalledWith(
        "DownloadableTestModel",
      ),
    );
  });
});
