/**
 * The form half of searching a parameter chosen out of a set.
 *
 * HPO worked for integers and floats only, and the form is one of the reasons:
 * the optimizer control asks for a lower and an upper bound, which is the only
 * shape a search space has ever had here. `hinge` is not between
 * `squared_hinge` and anything else, so there was nothing a user could type.
 *
 * What these tests pin down is the part only the form can get wrong: which
 * control a field gets, that the envelope written when the toggle is flipped
 * carries the keys belonging to that kind of space and no others, and that a
 * field which also admits null still reaches the optimizer control at all.
 */

import React from "react";
import { screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

// react-markdown ships ESM only and Create React App's jest does not transform
// node_modules, so importing any form component pulls in a parse error before a
// single assertion runs. See FormSchemaRenderFields.test.jsx for the full note.
jest.mock("react-markdown", () => ({
  __esModule: true,
  default: ({ children }) => <span>{children}</span>,
}));

import { renderWithProviders } from "../../test-utils/renderWithProviders";
import FormSchemaRenderFields from "./FormSchemaRenderFields";
import { formattedModel, generateYupSchema } from "../../utils/schema";
import { linearSvcWireSchema } from "../../utils/linearSvcSchema.fixture";
import { decisionTreeWireSchema } from "../../utils/decisionTreeSchema.fixture";

const BASE_VALUES = {
  C: {
    optimize: false,
    fixed_value: 1.0,
    lower_bound: 0.01,
    upper_bound: 100.0,
  },
  loss: {
    optimize: false,
    fixed_value: "squared_hinge",
    choices: ["squared_hinge", "hinge"],
  },
  fit_intercept: { optimize: false, fixed_value: true, choices: [false, true] },
  class_weight: {
    optimize: false,
    fixed_value: null,
    choices: [null, "balanced"],
  },
};

function fakeFormik(values, errors = {}) {
  return { values, errors, setFieldValue: jest.fn() };
}

/** What the renderer wrote for one field, ignoring formik's shouldValidate flag. */
const written = (formik, name) => {
  const call = formik.setFieldValue.mock.calls.find(([key]) => key === name);
  return call?.[1];
};

async function renderForm({ values = BASE_VALUES, errors = {} } = {}) {
  const modelSchema = await formattedModel(linearSvcWireSchema);
  const formik = fakeFormik(values, errors);
  const result = renderWithProviders(
    <FormSchemaRenderFields
      modelSchema={modelSchema}
      formik={formik}
      handleUpdateSchema={jest.fn()}
    />,
  );
  return { ...result, formik, modelSchema };
}

// The label appears more than once by design: once in the card header and once
// as the outlined input's legend, which the card hides with CSS.
const cardFor = (label) =>
  screen.getAllByText(label)[0].closest(".MuiPaper-root");

// --------------------------------------------------------------------------- //
// Which control a field gets
// --------------------------------------------------------------------------- //

describe("a categorical parameter in the optimizer form", () => {
  it("gives every optimizable field an optimize toggle", async () => {
    await renderForm();
    // One per field, all four of them, including the two that could not be
    // searched at all before.
    expect(screen.getAllByRole("switch")).toHaveLength(4);
  });

  it("shows the options by name rather than by raw value", async () => {
    await renderForm();
    const card = cardFor("Loss");
    expect(within(card).getByText("Squared hinge")).toBeInTheDocument();
  });

  it("names the two values of a boolean parameter", async () => {
    await renderForm({
      values: {
        ...BASE_VALUES,
        fit_intercept: { ...BASE_VALUES.fit_intercept, optimize: false },
      },
    });
    const card = cardFor("Fit intercept");
    expect(within(card).getByText("True")).toBeInTheDocument();
  });

  it("still gives a numeric parameter its bounds when optimizing", async () => {
    const { container } = await renderForm({
      values: { ...BASE_VALUES, C: { ...BASE_VALUES.C, optimize: true } },
    });
    expect(container.querySelector('input[name="C-lower"]')).not.toBeNull();
    expect(container.querySelector('input[name="C-upper"]')).not.toBeNull();
  });

  it("gives a categorical parameter options instead of bounds", async () => {
    const { container } = await renderForm({
      values: { ...BASE_VALUES, loss: { ...BASE_VALUES.loss, optimize: true } },
    });
    expect(container.querySelector('input[name="loss-lower"]')).toBeNull();
    expect(
      within(cardFor("Loss")).getByText("Options to search"),
    ).toBeInTheDocument();
  });

  it("lists the searched options as chips, by name", async () => {
    await renderForm({
      values: { ...BASE_VALUES, loss: { ...BASE_VALUES.loss, optimize: true } },
    });
    const card = cardFor("Loss");
    expect(within(card).getByText("Squared hinge")).toBeInTheDocument();
    expect(within(card).getByText("Hinge")).toBeInTheDocument();
  });
});

// --------------------------------------------------------------------------- //
// A field that also admits null
// --------------------------------------------------------------------------- //

describe("an optimizable field that also admits null", () => {
  it("reaches the optimizer control rather than the union picker", async () => {
    /**
     * The renderer used to test `anyOf` before `isOptimizable`, so a nullable
     * field always went to the union picker. That cost nothing while every
     * such field carried `placeholder=None` — which is exactly why the
     * thirty-one fields declared `none_type(optimizer_int_field(...))` could
     * never be optimized.
     */
    await renderForm();
    const card = cardFor("Class weight");
    expect(within(card).getByRole("switch")).toBeInTheDocument();
  });

  it("offers null in the menu, with a name, so it can be ticked back", async () => {
    /**
     * Asserted on the menu rather than on the chips. The chips are drawn from
     * the value, so they show null whatever the menu offers; taking the option
     * list from `enum` left null out of the menu, and a user who unticked it
     * could not get it back.
     *
     * Unweighted against balanced is the comparison worth searching here, and
     * read as a one-option enum there would be nothing to search at all.
     */
    await renderForm({
      values: {
        ...BASE_VALUES,
        class_weight: { ...BASE_VALUES.class_weight, optimize: true },
      },
    });
    await userEvent.click(
      within(cardFor("Class weight")).getByRole("combobox"),
    );
    const menu = within(await screen.findByRole("listbox"));
    expect(menu.getByText("None")).toBeInTheDocument();
    expect(
      menu.getByText("Weighted by inverse class frequency"),
    ).toBeInTheDocument();
  });

  it("names the options of a nullable enum despite the offset", async () => {
    /** `enumNames` is aligned with `enum`, which has one fewer entry than the
     * options once null joins them, so the names are matched by option. */
    await renderForm();
    await userEvent.click(
      within(cardFor("Class weight")).getByRole("combobox"),
    );
    const menu = within(await screen.findByRole("listbox"));
    expect(
      menu.getByText("Weighted by inverse class frequency"),
    ).toBeInTheDocument();
    expect(menu.queryByText("balanced")).toBeNull();
  });
});

// --------------------------------------------------------------------------- //
// What the toggle writes
// --------------------------------------------------------------------------- //

describe("flipping the optimize toggle", () => {
  it("writes choices and no bounds for a categorical parameter", async () => {
    const { formik } = await renderForm();
    await userEvent.click(within(cardFor("Loss")).getByRole("switch"));

    expect(written(formik, "loss")).toEqual({
      optimize: true,
      fixed_value: "squared_hinge",
      choices: ["squared_hinge", "hinge"],
    });
  });

  it("writes bounds and no choices for a numeric parameter", async () => {
    const { formik } = await renderForm();
    await userEvent.click(within(cardFor("C")).getByRole("switch"));

    expect(written(formik, "C")).toEqual({
      optimize: true,
      fixed_value: 1.0,
      lower_bound: 0.01,
      upper_bound: 100.0,
    });
  });

  it("falls back to the declared options when the value carries none", async () => {
    const { formik } = await renderForm({
      values: {
        ...BASE_VALUES,
        loss: { optimize: false, fixed_value: "hinge" },
      },
    });
    await userEvent.click(within(cardFor("Loss")).getByRole("switch"));

    expect(written(formik, "loss")).toEqual({
      optimize: true,
      fixed_value: "hinge",
      choices: ["squared_hinge", "hinge"],
    });
  });
});

// --------------------------------------------------------------------------- //
// Validation
// --------------------------------------------------------------------------- //

describe("validating a categorical search", () => {
  const validate = async (values) => {
    // `generateYupSchema` iterates the flattened properties, which is what
    // `formattedModel` produces, rather than the whole JSON Schema object.
    const { schema } = generateYupSchema(
      await formattedModel(linearSvcWireSchema),
    );
    try {
      await schema.validate(values, { abortEarly: false });
      return [];
    } catch (error) {
      return error.errors ?? [error.message];
    }
  };

  it("accepts the declared defaults", async () => {
    expect(await validate(BASE_VALUES)).toEqual([]);
  });

  it("accepts a search over two options", async () => {
    const errors = await validate({
      ...BASE_VALUES,
      loss: {
        optimize: true,
        fixed_value: null,
        choices: ["squared_hinge", "hinge"],
      },
    });
    expect(errors).toEqual([]);
  });

  it("rejects a search over a single option", async () => {
    const errors = await validate({
      ...BASE_VALUES,
      loss: { optimize: true, fixed_value: null, choices: ["hinge"] },
    });
    expect(errors.join(" ")).toMatch(/at least two/i);
  });

  it("rejects a search over an option the field does not offer", async () => {
    const errors = await validate({
      ...BASE_VALUES,
      loss: { optimize: true, fixed_value: null, choices: ["hinge", "hnge"] },
    });
    expect(errors.length).toBeGreaterThan(0);
  });

  it("leaves the numeric bounds check alone", async () => {
    const errors = await validate({
      ...BASE_VALUES,
      C: {
        optimize: true,
        fixed_value: 1.0,
        lower_bound: 100.0,
        upper_bound: 0.01,
      },
    });
    expect(errors.join(" ")).toMatch(/lower bound/i);
  });
});

// --------------------------------------------------------------------------- //
// A numeric parameter that also admits null
// --------------------------------------------------------------------------- //

describe("a nullable numeric search space", () => {
  /**
   * The shape the audit of the thirty-one produced: thirteen parameters that
   * are real hyperparameters, admit null, and now declare a range.
   * `max_depth=None` means no limit, so the null had to survive being made
   * searchable.
   */
  const DEPTH_VALUES = {
    max_depth: {
      optimize: false,
      fixed_value: null,
      lower_bound: 1,
      upper_bound: 32,
    },
    max_leaf_nodes: {
      optimize: false,
      fixed_value: null,
      lower_bound: 2,
      upper_bound: 255,
    },
    min_samples_split: {
      optimize: false,
      fixed_value: 2,
      lower_bound: 2,
      upper_bound: 20,
    },
  };

  const validateDepth = async (values) => {
    const { schema } = generateYupSchema(
      await formattedModel(decisionTreeWireSchema),
    );
    try {
      await schema.validate(values, { abortEarly: false });
      return [];
    } catch (error) {
      return error.errors ?? [error.message];
    }
  };

  it("gets the numeric bounds control rather than the union picker", async () => {
    const modelSchema = await formattedModel(decisionTreeWireSchema);
    const { container } = renderWithProviders(
      <FormSchemaRenderFields
        modelSchema={modelSchema}
        formik={fakeFormik({
          ...DEPTH_VALUES,
          max_depth: { ...DEPTH_VALUES.max_depth, optimize: true },
        })}
        handleUpdateSchema={jest.fn()}
      />,
    );
    expect(
      container.querySelector('input[name="max_depth-lower"]'),
    ).not.toBeNull();
    expect(
      container.querySelector('input[name="max_depth-upper"]'),
    ).not.toBeNull();
  });

  it("accepts the declared defaults, null fixed value and all", async () => {
    expect(await validateDepth(DEPTH_VALUES)).toEqual([]);
  });

  it("enforces the bounds declared inside the anyOf branch", async () => {
    /**
     * `minimum` sits in the `anyOf` branch for a field that also admits null,
     * so reading it only off the property left these thirteen parameters with
     * no bounds enforced in the form at all: a depth of -3 reached the backend
     * before anything objected.
     */
    const errors = await validateDepth({
      ...DEPTH_VALUES,
      max_depth: {
        optimize: true,
        fixed_value: null,
        lower_bound: -3,
        upper_bound: 32,
      },
    });
    expect(errors.length).toBeGreaterThan(0);
  });

  it("still enforces them on a field that never admitted null", async () => {
    const errors = await validateDepth({
      ...DEPTH_VALUES,
      min_samples_split: {
        optimize: true,
        fixed_value: 2,
        lower_bound: 0,
        upper_bound: 20,
      },
    });
    expect(errors.length).toBeGreaterThan(0);
  });
});
