import React from "react";
import { screen } from "@testing-library/react";
import { renderWithProviders } from "../test-utils/renderWithProviders";
import ResponsiveAppBar from "./ResponsiveAppBar";

// CredentialsButton and UpdatesButton pull in the axios-based api client,
// notistack and react-markdown, which ship ESM that CRA's Jest does not
// transform. They are not under test here, so stub them out (mirrors how other
// suites mock their api-bound children).
jest.mock("./credentials/CredentialsButton", () => () => null);
jest.mock("./updates/UpdatesButton", () => () => null);

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
