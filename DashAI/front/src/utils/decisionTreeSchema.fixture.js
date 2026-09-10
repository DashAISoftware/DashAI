/**
 * The exact payload `GET /api/v1/component?model=DecisionTreeRegression` serves,
 * after the backend's `localize()` collapsed every MultilingualString to
 * English, trimmed to three fields.
 *
 * Two of them are the shape the audit produced: a parameter that admits null
 * *and* declares a search space, which no field was before. `max_depth=None`
 * means no limit, so the null had to survive being made searchable, and its
 * bounds live in the `anyOf` branch rather than on the property.
 *
 * Captured from the running backend rather than hand-written, so a test built
 * on it fails if the wire format drifts instead of passing against a shape
 * nobody serves. Regenerate with:
 *
 *   uv run python -c "import json; \
 *     from DashAI.back.models.scikit_learn.decision_tree_regression import \
 *       DecisionTreeRegression as M; \
 *     from DashAI.back.core.utils import localize; \
 *     print(json.dumps(localize(M.get_schema(), 'en')))"
 */

export const decisionTreeWireSchema = {
  description:
    "Schema that configures the Decision Tree Regressor.\n\nThe Decision Tree Regressor builds a tree by recursively splitting the feature\nspace to minimise MSE (or MAE) at each node. The underlying implementation is\n``sklearn.tree.DecisionTreeRegressor``.",
  properties: {
    max_depth: {
      anyOf: [
        {
          minimum: 1,
          type: "integer",
        },
        {
          type: "null",
        },
      ],
      description:
        "The maximum depth of the tree. If None, nodes are expanded until all leaves are pure or fewer than min_samples_split samples remain.",
      placeholder: {
        fixed_value: null,
        lower_bound: 1,
        optimize: false,
        upper_bound: 32,
      },
      "x-dashai-search-dtype": "integer",
      title: "Max depth",
    },
    max_leaf_nodes: {
      anyOf: [
        {
          minimum: 2,
          type: "integer",
        },
        {
          type: "null",
        },
      ],
      description:
        "Grow a tree with at most max_leaf_nodes in best-first fashion. If None, unlimited leaf nodes.",
      placeholder: {
        fixed_value: null,
        lower_bound: 2,
        optimize: false,
        upper_bound: 255,
      },
      "x-dashai-search-dtype": "integer",
      title: "Max leaf nodes",
    },
    min_samples_split: {
      description:
        "Minimum number of samples required to split an internal node.",
      minimum: 2,
      placeholder: {
        fixed_value: 2,
        lower_bound: 2,
        optimize: false,
        upper_bound: 20,
      },
      type: "integer",
      "x-dashai-search-dtype": "integer",
      title: "Min samples split",
    },
  },
  required: ["max_depth", "min_samples_split", "max_leaf_nodes"],
  title: "DecisionTreeRegressionSchema",
  type: "object",
};
