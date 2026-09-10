import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../../test-utils/renderWithProviders";

// Mutable job list the mocked useJobManager returns; set per test.
let mockJobs = [];

// Mock API modules before importing component
jest.mock("../../api/job", () => ({
  deleteJob: jest.fn(),
  deleteAllJobs: jest.fn(),
  getJobs: jest.fn(() => Promise.resolve([])),
}));

jest.mock("../../hooks/useJobPolling", () => ({
  useJobManager: () => ({
    jobs: mockJobs,
    loading: false,
    error: null,
    refresh: jest.fn(),
  }),
}));

import JobQueueWidget from "./JobQueueWidget";

beforeEach(() => {
  mockJobs = [];
  // Ensure the job list is expanded so rows (and their bars) render.
  localStorage.setItem("jobQueueWidgetExpanded", "true");
});

describe("JobQueueWidget", () => {
  it("renders without crashing", () => {
    renderWithProviders(<JobQueueWidget />);
  });

  it("renders the Job Queue header", () => {
    renderWithProviders(<JobQueueWidget />);
    expect(screen.getByText("Job Queue")).toBeInTheDocument();
  });

  it("shows a determinate bar and phase message for a running job", () => {
    mockJobs = [
      {
        id: "job-1",
        task_type: "ModelJob",
        job_name: "Train model",
        status: "started",
        last_update: "2026-07-01 00:00:00.000",
        progress: 42,
        progress_message: "Training",
      },
    ];
    renderWithProviders(<JobQueueWidget />);

    expect(screen.getByText("Training")).toBeInTheDocument();
    const bar = screen.getByRole("progressbar");
    expect(bar).toHaveAttribute("aria-valuenow", "42");
  });

  it("shows an indeterminate bar when a running job has no progress", () => {
    mockJobs = [
      {
        id: "job-2",
        task_type: "ModelJob",
        job_name: "Train model",
        status: "started",
        last_update: "2026-07-01 00:00:00.000",
        progress: null,
        progress_message: null,
      },
    ];
    renderWithProviders(<JobQueueWidget />);

    const bar = screen.getByRole("progressbar");
    expect(bar).not.toHaveAttribute("aria-valuenow");
  });
});
