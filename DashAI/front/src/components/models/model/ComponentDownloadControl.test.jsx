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

import ComponentDownloadControl from "./ComponentDownloadControl";
import {
  downloadComponent,
  deleteComponentDownload,
} from "../../../api/component";

const component = {
  name: "OpusMtEnRoaTransformer",
  downloaded: false,
  metadata: { requires_download: true, download_size_bytes: 310000000 },
};

describe("ComponentDownloadControl", () => {
  it("shows a download button with the size and triggers download", async () => {
    renderWithProviders(
      <ComponentDownloadControl
        component={component}
        onStatusChange={() => {}}
      />,
    );
    const button = await screen.findByRole("button", { name: /download/i });
    fireEvent.click(button);
    await waitFor(() =>
      expect(downloadComponent).toHaveBeenCalledWith("OpusMtEnRoaTransformer"),
    );
  });

  it("shows a delete control for a downloaded component and deletes it", async () => {
    // A distinct name avoids the module-level download-state cache carrying
    // over from the download test above.
    const downloadedComponent = {
      ...component,
      name: "OpusMtEnRoaTransformerDownloaded",
      downloaded: true,
    };
    renderWithProviders(
      <ComponentDownloadControl
        component={downloadedComponent}
        onStatusChange={() => {}}
      />,
    );
    const button = await screen.findByRole("button", {
      name: /delete download/i,
    });
    fireEvent.click(button);
    // Deletion only happens after confirming in the modal.
    expect(deleteComponentDownload).not.toHaveBeenCalled();
    const confirm = await screen.findByRole("button", { name: "Delete" });
    fireEvent.click(confirm);
    await waitFor(() =>
      expect(deleteComponentDownload).toHaveBeenCalledWith(
        "OpusMtEnRoaTransformerDownloaded",
      ),
    );
  });
});
