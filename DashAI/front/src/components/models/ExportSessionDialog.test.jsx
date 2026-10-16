import React from "react";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";
import ExportSessionDialog from "./ExportSessionDialog";
import { getSessionExportPreview } from "../../api/modelSession";

jest.mock("notistack", () => {
  const snackbar = { enqueueSnackbar: jest.fn() };
  return { useSnackbar: () => snackbar };
});

jest.mock("../../api/modelSession", () => ({
  getSessionExportPreview: jest.fn(),
  exportModelSession: jest.fn(),
}));

const preview = {
  session_name: "Iris session",
  dataset_name: "iris",
  runs: [
    {
      id: 1,
      name: "Trained KNN",
      status: "FINISHED",
      goal_metric: "Accuracy",
      goal_metric_value: 0.9,
      in_progress: false,
      with_model: true,
      missing_model_file: false,
    },
    {
      id: 2,
      name: "Busy SVC",
      status: "STARTED",
      goal_metric: "Accuracy",
      goal_metric_value: null,
      in_progress: true,
      with_model: false,
      missing_model_file: false,
    },
  ],
  size_bytes: { with_models: 2048, recipe_only: 1024 },
};

describe("ExportSessionDialog", () => {
  beforeEach(() => {
    getSessionExportPreview.mockResolvedValue(preview);
  });

  it("disables runs in progress and Export when no run is chosen", async () => {
    renderWithProviders(
      <ExportSessionDialog open sessionId={7} onClose={() => {}} />,
    );

    const trained = await screen.findByRole("checkbox", {
      name: /Trained KNN/,
    });
    expect(trained).toBeChecked();
    expect(screen.getByRole("checkbox", { name: /Busy SVC/ })).toBeDisabled();

    const exportButton = screen.getByRole("button", { name: "Export" });
    expect(exportButton).toBeEnabled();

    fireEvent.click(screen.getByRole("button", { name: "None" }));
    expect(exportButton).toBeDisabled();

    fireEvent.click(screen.getByRole("button", { name: "Select all" }));
    expect(exportButton).toBeEnabled();
    expect(
      screen.getByRole("checkbox", { name: /Busy SVC/ }),
    ).not.toBeChecked();
  });
});
