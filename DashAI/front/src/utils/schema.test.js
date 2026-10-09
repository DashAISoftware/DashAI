/**
 * The schema pipeline, end to end: the payload the backend actually serves goes
 * in, and a Yup schema that enforces the component's declared cross-field rules
 * comes out.
 *
 * This is the seam the whole design rests on, and it is easy to break silently:
 * `formattedModel` flattens the JSON Schema down to its properties, so anything
 * living at the root — the rule set included — is dropped unless it is carried
 * across deliberately. A regression here does not throw; it just means no rule
 * ever fires in the browser again.
 */

import { validateYupSchema, yupToFormErrors } from "formik";

import {
  SCHEMA_RULES,
  emptyValueFor,
  getValidator,
  formattedModel,
  generateYupSchema,
  getSchemaRules,
  normalizeEmptyValue,
} from "./schema";
import {
  holdoutWireSchema,
  holdoutWireSchemaWithoutRules,
} from "./holdoutSchema.fixture";

/** Validate the way formik does, and return its per-field error object. */
async function errorsFor(schema, values) {
  try {
    await validateYupSchema(values, schema);
    return {};
  } catch (error) {
    return yupToFormErrors(error);
  }
}

const complete = {
  train: 0.6,
  validation: 0.3,
  test: 0.1,
  stratify: false,
  shuffle: true,
  random_state: 42,
};

describe("formattedModel carries the rule set across the flattening", () => {
  it("keeps the rules without turning them into a field", async () => {
    const formatted = await formattedModel(holdoutWireSchema);

    expect(getSchemaRules(formatted)).toHaveLength(3);
    // The loops that render one input per entry must not see them.
    expect(Object.keys(formatted)).toEqual([
      "train",
      "test",
      "validation",
      "stratify",
      "shuffle",
      "random_state",
    ]);
    expect(JSON.stringify(formatted)).not.toContain("x-dashai-rules");
    expect(Object.keys(formatted)).not.toContain("x-dashai-rules");
  });

  it("survives being spread, which several consumers do", async () => {
    const formatted = await formattedModel(holdoutWireSchema);
    expect(getSchemaRules({ ...formatted })).toHaveLength(3);
  });

  it("reports an empty rule set for a schema that declares none", async () => {
    const formatted = await formattedModel(holdoutWireSchemaWithoutRules);
    expect(getSchemaRules(formatted)).toEqual([]);
    expect(formatted[SCHEMA_RULES]).toEqual([]);
  });

  it("still marks required fields the way the renderer expects", async () => {
    const formatted = await formattedModel(holdoutWireSchema);
    expect(formatted.train.required).toBe(true);
    expect(formatted.train.placeholder).toBe(0.6);
    expect(formatted.train.title).toBe("Train");
  });
});

describe("generateYupSchema enforces the declared rules", () => {
  it("seeds the initial values from the placeholders", async () => {
    const { initialValues } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    expect(initialValues).toEqual({
      train: 0.6,
      test: 0.2,
      validation: 0.2,
      stratify: false,
      shuffle: true,
      random_state: 42,
    });
  });

  it("accepts the seeded defaults", async () => {
    const { schema, initialValues } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    await expect(errorsFor(schema, initialValues)).resolves.toEqual({});
  });

  it("accepts 60/30/10, which the pipeline editor's exact check rejects", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    expect(0.6 + 0.3 + 0.1).not.toBe(1);
    await expect(errorsFor(schema, complete)).resolves.toEqual({});
  });

  it("reports the sum under all three partitions, with the total quoted", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    const errors = await errorsFor(schema, { ...complete, test: 0.3 });

    expect(Object.keys(errors).sort()).toEqual(["test", "train", "validation"]);
    expect(errors.train).toBe(
      "Train, validation and test must sum to 1 (they currently add up to 1.2).",
    );
    expect(errors.validation).toBe(errors.train);
  });

  it("reports an empty train partition on its own field", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    const errors = await errorsFor(schema, {
      ...complete,
      train: 0,
      validation: 0.5,
      test: 0.5,
    });
    expect(errors.train).toBe("The train proportion must be greater than 0.");
    expect(errors.validation).toBeUndefined();
  });

  it("stops requiring the seed once shuffling is off", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );

    const shuffling = await errorsFor(schema, {
      ...complete,
      random_state: null,
    });
    expect(shuffling.random_state).toBeDefined();

    const notShuffling = await errorsFor(schema, {
      ...complete,
      shuffle: false,
      random_state: null,
    });
    expect(notShuffling.random_state).toBeUndefined();
  });

  it("changes nothing for a schema that declares no rules", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchemaWithoutRules),
    );
    // A sum of 1.2 is only a problem because a rule says so; without the rule
    // each proportion is valid on its own and the form submits.
    await expect(
      errorsFor(schema, { ...complete, test: 0.3 }),
    ).resolves.toEqual({});
  });

  it("still enforces the per-field bounds the JSON Schema declares", async () => {
    const { schema } = generateYupSchema(
      await formattedModel(holdoutWireSchema),
    );
    const errors = await errorsFor(schema, { ...complete, train: 1.4 });
    // The field's own constraint wins on its own field; the relation is
    // reported on the siblings.
    expect(errors.train).toMatch(/less than or equal to 1/);
    expect(errors.validation).toMatch(/must sum to 1/);
  });
});

describe("what an emptied input means, derived from the schema", () => {
  // The old question, answered from data instead of by a global rule. The
  // schema already says whether null is allowed and what the author chose as
  // the default; between those two facts there is no ambiguity left.
  const nullableColumn = {
    anyOf: [{ type: "string" }, { type: "null" }],
    placeholder: null,
  };
  const nullablePrompt = {
    anyOf: [{ type: "string" }, { type: "null" }],
    placeholder: "",
  };
  const plainString = { type: "string", placeholder: "abc" };
  const nullableInt = {
    anyOf: [{ type: "integer" }, { type: "null" }],
    placeholder: null,
  };

  it("means unset for a nullable field whose default is not the empty string", () => {
    // group_column and the other 76 string-or-null fields: an empty string
    // here is a column named "", which is what reached sklearn.
    expect(emptyValueFor(nullableColumn)).toBeNull();
    expect(emptyValueFor(nullableInt)).toBeNull();
  });

  it("means the empty string when the author chose it as the default", () => {
    // The 14 negative_prompt fields across the diffusion models. A single
    // global "empty means null" rule would be wrong for exactly these.
    expect(emptyValueFor(nullablePrompt)).toBe("");
  });

  it("leaves a non-nullable field alone", () => {
    expect(emptyValueFor(plainString)).toBe("");
  });

  it("tolerates a field it knows nothing about", () => {
    expect(emptyValueFor(undefined)).toBe("");
    expect(emptyValueFor({})).toBe("");
  });

  it("only rewrites empty values, never real ones", () => {
    expect(normalizeEmptyValue("abc", nullableColumn)).toBe("abc");
    expect(normalizeEmptyValue(0, nullableInt)).toBe(0);
    expect(normalizeEmptyValue(false, nullableColumn)).toBe(false);
    expect(normalizeEmptyValue(null, nullableColumn)).toBeNull();
  });

  it("treats a cleared box and an absent value the same way", () => {
    expect(normalizeEmptyValue("", nullableColumn)).toBeNull();
    expect(normalizeEmptyValue(undefined, nullableColumn)).toBeNull();
    expect(normalizeEmptyValue("", nullablePrompt)).toBe("");
    expect(normalizeEmptyValue(undefined, nullablePrompt)).toBe("");
  });
});

describe("multipleOf, the standard keyword nobody was emitting", () => {
  // The diffusion models' image sizes must be multiples of 8 because the VAE
  // downsamples by that factor. That was stated in the description in five
  // languages, checked nowhere, and 28 properties carried it. It is a per-field
  // type constraint, not a relation between fields, so it belongs in the
  // schema's own vocabulary rather than in the rule engine.
  const imageSize = {
    type: "integer",
    minimum: 64,
    maximum: 2048,
    multipleOf: 8,
    required: true,
  };

  const check = async (value) => {
    try {
      await getValidator(imageSize).validate(value);
      return null;
    } catch (error) {
      return error.message;
    }
  };

  it("accepts a multiple", async () => {
    await expect(check(1024)).resolves.toBeNull();
    await expect(check(64)).resolves.toBeNull();
    await expect(check(512)).resolves.toBeNull();
  });

  it("rejects a value the pipeline could not honour", async () => {
    await expect(check(513)).resolves.toBe("Must be a multiple of 8");
    await expect(check(1020)).resolves.toBe("Must be a multiple of 8");
  });

  it("still enforces the bounds alongside it", async () => {
    await expect(check(32)).resolves.toMatch(/greater than or equal to 64/);
    await expect(check(4096)).resolves.toMatch(/less than or equal to 2048/);
  });

  it("leaves a field without the keyword alone", async () => {
    const plain = { type: "integer", minimum: 1, required: true };
    let message = null;
    try {
      await getValidator(plain).validate(7);
    } catch (error) {
      message = error.message;
    }
    expect(message).toBeNull();
  });
});

describe("an empty string that is itself an option", () => {
  // Plotly's histnorm offers "" as a real value meaning raw counts, and it is
  // the default. Treating it as emptiness made the option unselectable: the
  // form sent null, the backend rejected it for a field that does not admit
  // one, and there was no way back to the default.
  const histnorm = {
    type: "string",
    enum: ["", "percent", "probability", "density", "probability density"],
    enumNames: [
      "Count",
      "Percent",
      "Probability",
      "Density",
      "Probability density",
    ],
    placeholder: "",
  };

  it("keeps the empty string as a value", () => {
    expect(emptyValueFor(histnorm)).toBe("");
    expect(normalizeEmptyValue("", histnorm)).toBe("");
  });

  it("still means unset for a nullable enum that does not offer it", () => {
    const nullableEnum = {
      anyOf: [{ type: "string", enum: ["sqrt", "log2"] }, { type: "null" }],
      placeholder: null,
    };
    expect(emptyValueFor(nullableEnum)).toBeNull();
  });

  it("wins over nullability, so the two layers cannot disagree", () => {
    // Contrived: an enum offering "" on a field that also admits null. The
    // option is a value, so it must survive either way.
    const both = {
      anyOf: [{ type: "string", enum: ["", "x"] }, { type: "null" }],
      placeholder: null,
    };
    expect(emptyValueFor(both)).toBe("");
  });
});
