/**
 * The exact payload `GET /api/v1/component?model=LinearSVCClassifier` serves,
 * after the backend's `localize()` collapsed every MultilingualString to
 * English, trimmed to the four fields these tests exercise.
 *
 * It is the model the categorical search was built for: `loss` offers
 * `squared_hinge` and `hinge`, which is exactly the comparison that could not
 * be searched before, and `C` still carries the hand-written interval
 * placeholder so both kinds of space appear in one form.
 *
 * Captured from the running backend rather than hand-written, so a test built
 * on it fails if the wire format drifts instead of passing against a shape
 * nobody serves. Regenerate with:
 *
 *   uv run python -c "import json; \
 *     from DashAI.back.models.scikit_learn.linear_svc_classifier import \
 *       LinearSVCClassifier as M; \
 *     from DashAI.back.core.utils import localize; \
 *     print(json.dumps(localize(M.get_schema(), 'en')))"
 */

export const linearSvcWireSchema = {
  description:
    "Schema that configures the Linear SVC Classifier.\n\nLinearSVC implements a linear Support Vector Classification trained with a\nlinear kernel. It is faster than kernel SVC for large datasets. Because\nLinearSVC does not natively expose class probabilities, it is calibrated with\nPlatt scaling (CalibratedClassifierCV). The underlying implementation is\n``sklearn.svm.LinearSVC``.",
  properties: {
    C: {
      description:
        "Regularisation parameter. The strength of the regularisation is inversely proportional to C. Must be strictly positive.",
      minimum: 0.0001,
      placeholder: {
        fixed_value: 1.0,
        lower_bound: 0.01,
        optimize: false,
        upper_bound: 100.0,
      },
      title: "C",
      type: "number",
    },
    loss: {
      description:
        "Specifies the loss function. 'squared_hinge' is the default; 'hinge' is the standard SVM loss.",
      enum: ["squared_hinge", "hinge"],
      enumNames: ["Squared hinge", "Hinge"],
      placeholder: {
        choices: ["squared_hinge", "hinge"],
        fixed_value: "squared_hinge",
        optimize: false,
      },
      type: "string",
      "x-dashai-search-dtype": "categorical",
      title: "Loss",
    },
    fit_intercept: {
      description:
        "Whether to calculate the intercept for this model. If False, the data is expected to be already centred.",
      placeholder: {
        choices: [false, true],
        fixed_value: true,
        optimize: false,
      },
      type: "boolean",
      "x-dashai-search-dtype": "categorical",
      title: "Fit intercept",
    },
    class_weight: {
      anyOf: [
        {
          enum: ["balanced"],
          enumNames: ["Weighted by inverse class frequency"],
          type: "string",
        },
        {
          type: "null",
        },
      ],
      description:
        "Weights associated with classes, used to correct for class imbalance. 'balanced' automatically adjusts weights inversely proportional to class frequencies. Use None for no weighting.",
      placeholder: {
        choices: [null, "balanced"],
        fixed_value: null,
        optimize: false,
      },
      "x-dashai-search-dtype": "categorical",
      title: "Class weight",
    },
  },
  required: ["C", "loss", "fit_intercept", "class_weight"],
  title: "LinearSVCClassifierSchema",
  type: "object",
};
