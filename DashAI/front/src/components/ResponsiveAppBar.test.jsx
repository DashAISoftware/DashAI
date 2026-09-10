import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test-utils/renderWithProviders";
import ResponsiveAppBar from "./ResponsiveAppBar";

// CredentialsButton pulls in the axios-based api client and notistack, both of
// which ship ESM that CRA's Jest does not transform. It is not under test here,
// so stub it out (mirrors how other suites mock their api-bound children).
jest.mock("./credentials/CredentialsButton", () => () => null);

describe("ResponsiveAppBar", () => {
  it("renders without crashing", () => {
    renderWithProviders(<ResponsiveAppBar />);
  });

  it("renders nav links for main sections", () => {
    renderWithProviders(<ResponsiveAppBar />);
    expect(screen.getByRole("link", { name: /datasets/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /models/i })).toBeInTheDocument();
  });
});
