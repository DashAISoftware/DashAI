export const NUMERIC_TYPES = new Set(["Integer", "Float", "Decimal"]);
export const ENCODER_OPTIONS = ["one_hot", "label"];

// Op value -> i18n key suffix under datasets:table.op.*
export const NUMERIC_OPS = [
  { value: "equals", symbol: "=" },
  { value: "between", symbol: "⇿" },
  { value: "greaterThan", symbol: ">" },
  { value: "greaterThanOrEqualTo", symbol: ">=" },
  { value: "lessThan", symbol: "<" },
  { value: "lessThanOrEqualTo", symbol: "<=" },
  { value: "empty", symbol: "0" },
  { value: "notEmpty", symbol: "!0" },
];

export const TEXT_OPS = [
  { value: "contains", symbol: "*" },
  { value: "startsWith", symbol: "a" },
  { value: "endsWith", symbol: "z" },
  { value: "equals", symbol: "=" },
  { value: "empty", symbol: "0" },
  { value: "notEmpty", symbol: "!0" },
];

export const opsByType = (type) =>
  NUMERIC_TYPES.has(type) ? NUMERIC_OPS : TEXT_OPS;

export const defaultOpForType = (type) =>
  NUMERIC_TYPES.has(type) ? "equals" : "contains";

// Internal "empty"/"notEmpty" map to backend's "isEmpty"/"isNotEmpty".
export const toBackendOperator = (op) => {
  if (op === "empty") return "isEmpty";
  if (op === "notEmpty") return "isNotEmpty";
  return op;
};
