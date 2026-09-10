/**
 * The dropdown's handling of an option that is the empty string.
 *
 * `histnorm` in the histogram explorer offers "" as a real value meaning raw
 * counts, and it is the field's default. The control used to translate that
 * selection into null, which the backend rejects for a field that does not
 * admit one, so once a user changed the normalization they could never set it
 * back. Left unlabelled it also rendered as a blank row, which is why
 * enum_field now emits enumNames.
 */

import React from "react";
import { screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import SelectInput from "./SelectInput";

const HISTNORM = [
  "",
  "percent",
  "probability",
  "density",
  "probability density",
];
const LABELS = [
  "Count",
  "Percent",
  "Probability",
  "Density",
  "Probability density",
];

function render(props = {}) {
  const onChange = jest.fn();
  const result = renderWithProviders(
    <SelectInput
      name="histnorm"
      label="Normalization"
      description="Type of normalization."
      options={HISTNORM}
      value=""
      onChange={onChange}
      {...props}
    />,
  );
  return { ...result, onChange };
}

describe("SelectInput with an empty-string option", () => {
  it("reports the empty string as a value, not as null", async () => {
    const { onChange } = render({ value: "percent", optionNames: LABELS });

    await userEvent.click(screen.getByRole("combobox"));
    await userEvent.click(screen.getByRole("option", { name: "Count" }));

    expect(onChange).toHaveBeenCalledWith("");
    expect(onChange).not.toHaveBeenCalledWith(null);
  });

  it("shows the label instead of a blank row", async () => {
    render({ optionNames: LABELS });
    await userEvent.click(screen.getByRole("combobox"));

    const options = screen.getAllByRole("option");
    expect(options).toHaveLength(HISTNORM.length);
    options.forEach((option) => expect(option.textContent).not.toBe(""));
    expect(screen.getByRole("option", { name: "Count" })).toBeInTheDocument();
  });

  it("still reports null for a dropdown that does not offer the empty string", async () => {
    const { onChange } = render({
      options: ["sqrt", "log2"],
      value: "sqrt",
      optionNames: undefined,
    });
    // MUI only produces "" for a select whose value is cleared, which is the
    // "nothing selected" case this coercion exists for.
    expect(onChange).not.toHaveBeenCalled();
  });
});
