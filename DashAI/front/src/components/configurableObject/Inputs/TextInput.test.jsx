/**
 * The "required" hint an empty text box shows.
 *
 * TextInput used to flag every empty box as required, so a negative prompt,
 * which the backend accepts empty, showed a red error the form then ignored.
 */

import React from "react";
import { screen } from "@testing-library/react";

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import TextInput from "./TextInput";

function render(props = {}) {
  return renderWithProviders(
    <TextInput
      name="negative_prompt"
      label="Negative prompt"
      value=""
      onChange={jest.fn()}
      description="What to exclude"
      {...props}
    />,
  );
}

const REQUIRED = "negative_prompt is a required field";

test("an empty box on a field that must hold text is flagged", () => {
  render();
  expect(screen.getByText(REQUIRED)).toBeInTheDocument();
});

test("an empty box on a nullable field is not flagged", () => {
  render({ nullable: true });
  expect(screen.queryByText(REQUIRED)).not.toBeInTheDocument();
});

test("a disabled empty box is not flagged", () => {
  render({ disabled: true });
  expect(screen.queryByText(REQUIRED)).not.toBeInTheDocument();
});

test("a validation error still shows on a nullable field", () => {
  render({ nullable: true, error: "Too long" });
  expect(screen.getByText("Too long")).toBeInTheDocument();
});
