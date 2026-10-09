/**
 * The render half of the rule layer: what a Relevance rule does to the form.
 *
 * The errors a Check produces travel through formik, because the Yup schema
 * built in `generateYupSchema` already enforces them (covered in
 * `utils/schema.test.js`). What is asserted here is the part only the renderer
 * can do: leaving a field inert or out of the form when the schema says it
 * stopped being meaningful, and — the assertion that matters most — doing that
 * without touching what the user typed.
 *
 * That last one is not a hypothetical. The rival architecture this design was
 * chosen over made the server's echo the single value store, and its fatal flaw
 * was exactly this: set a seed, turn shuffling off and on again, and the seed
 * was gone. The rule layer here is read-only over form state by construction,
 * and this file is what keeps it that way.
 */

import React from "react";
import { screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// react-markdown ships ESM only and Create React App's jest does not transform
// node_modules, so importing any form component pulls in a parse error before a
// single assertion runs. Stubbing it here keeps the failure scoped and visible:
// the descriptions and rule messages this file asserts on are plain text, so a
// passthrough renders exactly what the real component would. Teaching jest to
// transform the unified/remark tree is the "extend the jest harness" item in the
// plan's phase 0, and it belongs in one config change rather than in this file.
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

import { renderWithProviders } from "../../test-utils/renderWithProviders";
import FormSchemaRenderFields from "./FormSchemaRenderFields";
import { formattedModel } from "../../utils/schema";
import { holdoutWireSchema } from "../../utils/holdoutSchema.fixture";

const BASE_VALUES = {
  train: 0.6,
  test: 0.2,
  validation: 0.2,
  stratify: false,
  shuffle: true,
  random_state: 42,
};

/**
 * A stand-in for formik that records writes instead of holding state, so a test
 * can assert exactly what the renderer tried to change.
 */
function fakeFormik(values, errors = {}) {
  return {
    values,
    errors,
    setFieldValue: jest.fn(),
  };
}

async function renderForm({ values = BASE_VALUES, errors = {}, ...rest } = {}) {
  const modelSchema = await formattedModel(holdoutWireSchema);
  const formik = fakeFormik(values, errors);
  const handleUpdateSchema = jest.fn();
  const result = renderWithProviders(
    <FormSchemaRenderFields
      modelSchema={modelSchema}
      formik={formik}
      handleUpdateSchema={handleUpdateSchema}
      {...rest}
    />,
  );
  return { ...result, formik, handleUpdateSchema, modelSchema };
}

const inputFor = (container, name) =>
  container.querySelector(`input[name="${name}"]`);

describe("FormSchemaRenderFields with a schema that declares rules", () => {
  it("renders one control per field", async () => {
    const { container } = await renderForm();
    for (const name of Object.keys(BASE_VALUES)) {
      expect(inputFor(container, name)).not.toBeNull();
    }
    // The label appears twice by design: once in the card header and once as
    // the outlined input's legend, which the card hides with CSS.
    expect(screen.getAllByText("Random state").length).toBeGreaterThan(0);
  });

  it("leaves every field enabled while the relevance condition holds", async () => {
    const { container } = await renderForm();
    expect(inputFor(container, "random_state")).not.toBeDisabled();
    expect(inputFor(container, "train")).not.toBeDisabled();
  });

  it("disables the seed once shuffling is off, and says why", async () => {
    const { container } = await renderForm({
      values: { ...BASE_VALUES, shuffle: false },
    });

    expect(inputFor(container, "random_state")).toBeDisabled();
    expect(
      screen.getByText(
        /random state has no effect while shuffling is disabled/i,
      ),
    ).toBeInTheDocument();
    // Only the field the rule names: the rest of the form is untouched.
    expect(inputFor(container, "train")).not.toBeDisabled();
    expect(inputFor(container, "stratify")).not.toBeDisabled();
  });

  it("keeps the user's seed visible while the field is inert", async () => {
    // The value is still the user's, so turning shuffling back on restores the
    // form exactly as they left it. A design that rewrote values here would
    // show 42, the placeholder, instead of 7.
    const { container } = await renderForm({
      values: { ...BASE_VALUES, shuffle: false, random_state: 7 },
    });
    expect(inputFor(container, "random_state")).toHaveValue(7);
  });

  it("never writes to form state while resolving relevance", async () => {
    const { formik, handleUpdateSchema } = await renderForm({
      values: { ...BASE_VALUES, shuffle: false, random_state: 7 },
    });
    // Rendering an irrelevant field must not look like the user changed
    // anything: no setFieldValue, no schema update, no submit.
    expect(formik.setFieldValue).not.toHaveBeenCalled();
    expect(handleUpdateSchema).not.toHaveBeenCalled();
  });

  it("removes a field whose rule asks to hide it", async () => {
    // Same rule, different effect. Built here rather than added to the fixture
    // because no shipped component asks to hide a field yet.
    const hidden = JSON.parse(JSON.stringify(holdoutWireSchema));
    hidden["x-dashai-rules"] = hidden["x-dashai-rules"].map((rule) =>
      rule.kind === "relevance" ? { ...rule, effect: "hide" } : rule,
    );
    const modelSchema = await formattedModel(hidden);
    const { container } = renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={modelSchema}
        formik={fakeFormik({ ...BASE_VALUES, shuffle: false })}
        handleUpdateSchema={jest.fn()}
      />,
    );

    expect(inputFor(container, "random_state")).toBeNull();
    expect(screen.queryAllByText("Random state")).toHaveLength(0);
    // Everything else still renders.
    expect(inputFor(container, "train")).not.toBeNull();
  });

  it("shows a formik error under the field it belongs to", async () => {
    await renderForm({
      values: { ...BASE_VALUES, test: 0.3 },
      errors: { train: "Must sum to 1 (they currently add up to 1.1)." },
    });
    expect(
      screen.getByText(/Must sum to 1 \(they currently add up to 1\.1\)\./),
    ).toBeInTheDocument();
  });

  it("still honours excludeFields, the hand-rendering escape hatch", async () => {
    const { container } = await renderForm({ excludeFields: ["train"] });
    expect(inputFor(container, "train")).toBeNull();
    expect(inputFor(container, "test")).not.toBeNull();
  });

  it("reports an edit through the normal formik path", async () => {
    const { container, formik, handleUpdateSchema } = await renderForm();
    const stratify = inputFor(container, "stratify");

    await userEvent.click(stratify);

    expect(formik.setFieldValue).toHaveBeenCalledWith("stratify", true, true);
    expect(handleUpdateSchema).toHaveBeenCalled();
  });
});

describe("FormSchemaRenderFields with a schema that declares no rules", () => {
  it("renders exactly as it did before the rule layer existed", async () => {
    const plain = JSON.parse(JSON.stringify(holdoutWireSchema));
    delete plain["x-dashai-rules"];
    const modelSchema = await formattedModel(plain);
    const { container } = renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={modelSchema}
        formik={fakeFormik({ ...BASE_VALUES, shuffle: false })}
        handleUpdateSchema={jest.fn()}
      />,
    );

    // With no relevance rule, shuffling being off means nothing to the form.
    expect(inputFor(container, "random_state")).not.toBeDisabled();
    expect(
      screen.queryByText(/random state has no effect/i),
    ).not.toBeInTheDocument();
  });

  it("tolerates a schema that has not loaded yet", () => {
    const { container } = renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={null}
        formik={fakeFormik({})}
        handleUpdateSchema={jest.fn()}
      />,
    );
    expect(within(container).queryAllByRole("textbox")).toHaveLength(0);
  });
});

describe("relevance on a union field, the SimpleImputer case", () => {
  // A four-branch union governed by an enum value rather than a boolean. It
  // renders through FormSchemaFieldWithOptions, a different branch of the
  // dispatcher than the holdout fields, so the disable effect has to reach the
  // type-selector chips as well as the input: leaving those live would let a
  // user switch the type and write a value into a field that means nothing.
  const imputerSchema = {
    title: "SimpleImputerSchema",
    type: "object",
    required: ["strategy", "fill_value"],
    properties: {
      strategy: {
        type: "string",
        enum: ["mean", "median", "most_frequent", "constant"],
        placeholder: "mean",
        title: "Strategy",
        description: "The imputation strategy.",
      },
      fill_value: {
        anyOf: [
          { type: "integer" },
          { type: "number" },
          { type: "string" },
          { type: "null" },
        ],
        placeholder: null,
        title: "Fill Value",
        description: "The value to replace missing values with.",
      },
    },
    "x-dashai-rules": [
      {
        kind: "relevance",
        field: "fill_value",
        when: {
          n: "cmp",
          op: "eq",
          a: { n: "field", f: "strategy" },
          b: { n: "lit", v: "constant" },
        },
        effect: "disable",
        reason:
          'The fill value is only used by the "constant" strategy; the others compute the replacement from the data.',
      },
    ],
  };

  async function renderImputer(values) {
    const modelSchema = await formattedModel(imputerSchema);
    return renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={modelSchema}
        formik={fakeFormik(values)}
        handleUpdateSchema={jest.fn()}
      />,
    );
  }

  it("disables the union input and its type chips under a non-constant strategy", async () => {
    const { container } = await renderImputer({
      strategy: "mean",
      fill_value: 99,
    });

    expect(inputFor(container, "fill_value")).toBeDisabled();
    const chips = screen.getAllByRole("button", {
      name: /Int|Float|String|Null/,
    });
    expect(chips.length).toBeGreaterThan(0);
    chips.forEach((chip) => expect(chip).toBeDisabled());
    expect(
      screen.getByText(/only used by the "constant" strategy/i),
    ).toBeInTheDocument();
  });

  it("keeps the value the user typed while the field is inert", async () => {
    const { container } = await renderImputer({
      strategy: "mean",
      fill_value: 99,
    });
    // sklearn discards this 99 silently; the form must not, or switching back
    // to "constant" would lose it.
    expect(inputFor(container, "fill_value")).toHaveValue(99);
  });

  it("enables it again under the constant strategy", async () => {
    const { container } = await renderImputer({
      strategy: "constant",
      fill_value: 99,
    });

    expect(inputFor(container, "fill_value")).not.toBeDisabled();
    screen
      .getAllByRole("button", { name: /Int|Float|String|Null/ })
      .forEach((chip) => expect(chip).not.toBeDisabled());
    expect(
      screen.queryByText(/only used by the "constant" strategy/i),
    ).not.toBeInTheDocument();
  });

  it("never disables the field the condition reads", async () => {
    const { container } = await renderImputer({
      strategy: "mean",
      fill_value: 99,
    });
    expect(inputFor(container, "strategy")).not.toBeDisabled();
  });
});

describe("an emptied nullable field", () => {
  // The oldest defect on this path: a cleared box handed back "" and the
  // backend stored a column named "", which sklearn then choked on. The
  // historical workaround displayed the word "none" for a null value, which
  // survived only because the null branch renders the input disabled.
  const nullableSchema = (placeholder) => ({
    title: "S",
    type: "object",
    required: ["group_column"],
    properties: {
      group_column: {
        anyOf: [{ type: "string" }, { type: "null" }],
        placeholder,
        title: "Group column",
        description: "The column to group by.",
      },
    },
  });

  async function renderNullable(value, placeholder = null) {
    const modelSchema = await formattedModel(nullableSchema(placeholder));
    const formik = fakeFormik({ group_column: value });
    const result = renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={modelSchema}
        formik={formik}
        handleUpdateSchema={jest.fn()}
      />,
    );
    return { ...result, formik };
  }

  it("shows an empty box for a null value, not the word none", async () => {
    const { container } = await renderNullable(null);
    const input = inputFor(container, "group_column");
    expect(input).toHaveValue("");
    expect(screen.queryByDisplayValue("none")).not.toBeInTheDocument();
  });

  it("stores null when the user clears it", async () => {
    const { container, formik } = await renderNullable("some_column");
    const input = inputFor(container, "group_column");
    expect(input).not.toBeDisabled();

    await userEvent.clear(input);

    await waitFor(() =>
      expect(formik.setFieldValue).toHaveBeenCalledWith(
        "group_column",
        null,
        true,
      ),
    );
    // Never the empty string, which is the value that used to reach sklearn.
    expect(formik.setFieldValue).not.toHaveBeenCalledWith(
      "group_column",
      "",
      true,
    );
  });

  it("keeps the empty string when the author chose it as the default", async () => {
    // The diffusion models' negative_prompt: same wire shape, opposite
    // meaning, which is why this is derived per field instead of globally.
    const { container, formik } = await renderNullable("a prompt", "");
    await userEvent.clear(inputFor(container, "group_column"));

    await waitFor(() =>
      expect(formik.setFieldValue).toHaveBeenCalledWith(
        "group_column",
        "",
        true,
      ),
    );
  });
});
