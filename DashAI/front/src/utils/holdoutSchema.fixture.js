/**
 * The exact payload `GET /api/v1/component?model=HoldoutSplitter` serves, after
 * the backend's `localize()` collapsed every MultilingualString to English.
 *
 * Captured from the running backend rather than hand-written, so a test built
 * on it fails if the wire format drifts instead of passing against a shape
 * nobody serves. Regenerate with:
 *
 *   uv run python -c "import json; \
 *     from DashAI.back.splitters.holdout import HoldoutSplitter; \
 *     from DashAI.back.core.utils import localize; \
 *     print(json.dumps(localize(HoldoutSplitter.get_schema(), 'en')))"
 */

const trainValidationTestSum = {
  n: "sum",
  of: [
    { f: "train", n: "field" },
    { f: "validation", n: "field" },
    { f: "test", n: "field" },
  ],
};

export const holdoutWireSchema = {
  title: "HoldoutSplitterSchema",
  type: "object",
  required: [
    "train",
    "test",
    "validation",
    "stratify",
    "shuffle",
    "random_state",
  ],
  properties: {
    train: {
      type: "number",
      minimum: 0.0,
      maximum: 1.0,
      placeholder: 0.6,
      title: "Train",
      description:
        "Proportion of the dataset assigned to the training partition.",
    },
    test: {
      type: "number",
      minimum: 0.0,
      maximum: 1.0,
      placeholder: 0.2,
      title: "Test",
      description: "Proportion of the dataset assigned to the test partition.",
    },
    validation: {
      type: "number",
      minimum: 0.0,
      maximum: 1.0,
      placeholder: 0.2,
      title: "Validation",
      description:
        "Proportion of the dataset assigned to the validation partition.",
    },
    stratify: {
      type: "boolean",
      placeholder: false,
      title: "Stratify",
      description:
        "Whether to preserve the class distribution across the splits.",
    },
    shuffle: {
      type: "boolean",
      placeholder: true,
      title: "Shuffle",
      description: "Whether to shuffle the data before splitting it.",
    },
    random_state: {
      type: "integer",
      minimum: 0,
      placeholder: 42,
      title: "Random state",
      description: "Seed used to make the split reproducible.",
    },
  },
  "x-dashai-rules": [
    {
      kind: "check",
      id: "holdout.proportions_sum_to_one",
      targets: ["train", "validation", "test"],
      message:
        "Train, validation and test must sum to 1 (they currently add up to {total}).",
      expr: {
        n: "approx",
        a: trainValidationTestSum,
        b: { n: "lit", v: 1.0 },
        tol: 1e-6,
      },
      bindings: { total: trainValidationTestSum },
      requires_ctx: false,
    },
    {
      kind: "check",
      id: "holdout.train_not_empty",
      targets: ["train"],
      message: "The train proportion must be greater than 0.",
      expr: {
        n: "cmp",
        op: "gt",
        a: { f: "train", n: "field" },
        b: { n: "lit", v: 0 },
      },
      bindings: {},
      requires_ctx: false,
    },
    {
      kind: "relevance",
      field: "random_state",
      when: { n: "is_true", of: { f: "shuffle", n: "field" } },
      effect: "disable",
      reason: "The random state has no effect while shuffling is disabled.",
    },
  ],
};

/** The same schema with its rules stripped, i.e. every other component today. */
export const holdoutWireSchemaWithoutRules = (() => {
  const copy = JSON.parse(JSON.stringify(holdoutWireSchema));
  delete copy["x-dashai-rules"];
  return copy;
})();
