import React from "react";
import { screen, fireEvent } from "@testing-library/react";
import { renderWithProviders } from "../../../test-utils/renderWithProviders";
import DivideDatasetColumns from "./DivideDatasetColumns";

describe("DivideDatasetColumns", () => {
  it("offers a converter's output group as an input column option, with its label and type chip", async () => {
    const onInputColumnNamesChange = jest.fn();
    renderWithProviders(
      <DivideDatasetColumns
        allColumnNames={["age"]}
        columnTypes={{
          age: { type: "Integer" },
          __group__0: { type: "Integer" },
        }}
        inputOptionNames={["age", "__group__0"]}
        optionLabels={{ __group__0: "Binarizador: output" }}
        selectedInputColumnNames={[]}
        onInputColumnNamesChange={onInputColumnNamesChange}
        selectedOutputColumnNames={[]}
        onOutputColumnNamesChange={() => {}}
      />,
    );

    const input = screen.getByLabelText(/Input Columns/i);
    fireEvent.mouseDown(input);
    fireEvent.click(await screen.findByText("Binarizador: output"));

    expect(onInputColumnNamesChange).toHaveBeenCalledWith(["__group__0"]);
  });

  it("does not offer converter groups as output column options", () => {
    renderWithProviders(
      <DivideDatasetColumns
        allColumnNames={["age"]}
        columnTypes={{
          age: { type: "Integer" },
          __group__0: { type: "Integer" },
        }}
        inputOptionNames={["age", "__group__0"]}
        optionLabels={{ __group__0: "Binarizador: output" }}
        selectedInputColumnNames={[]}
        onInputColumnNamesChange={() => {}}
        selectedOutputColumnNames={[]}
        onOutputColumnNamesChange={() => {}}
      />,
    );

    const output = screen.getByLabelText(/Output Columns/i);
    fireEvent.mouseDown(output);
    expect(screen.queryByText("Binarizador: output")).not.toBeInTheDocument();
  });

  it("falls back to allColumnNames for input options when inputOptionNames is not passed", () => {
    renderWithProviders(
      <DivideDatasetColumns
        allColumnNames={["age", "name"]}
        selectedInputColumnNames={[]}
        onInputColumnNamesChange={() => {}}
        selectedOutputColumnNames={[]}
        onOutputColumnNamesChange={() => {}}
      />,
    );

    const input = screen.getByLabelText(/Input Columns/i);
    fireEvent.mouseDown(input);
    expect(screen.getAllByText("age").length).toBeGreaterThan(0);
    expect(screen.getAllByText("name").length).toBeGreaterThan(0);
  });
});
