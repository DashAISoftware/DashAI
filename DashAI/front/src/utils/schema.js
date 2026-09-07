import * as Yup from "yup";
import { getComponents } from "../api/component";
import { withRules } from "./ruleEngine";

/**
 * Where a schema's cross-field rules travel once `formattedModel` has flattened
 * the JSON Schema down to its properties.
 *
 * A symbol key on purpose: every consumer of a formatted schema walks it with
 * `Object.keys` or `for...in` to render one field per entry, and both ignore
 * symbols, so the rules ride along without ever being mistaken for a field. It
 * is left enumerable so that a consumer which spreads the object (`{...schema}`)
 * keeps them.
 */
export const SCHEMA_RULES = Symbol.for("dashai.schemaRules");

/**
 * Read the cross-field rules off a formatted schema.
 *
 * @param {object} formattedSchema output of `formattedModel`
 * @returns {Array<object>} the rule set, empty when the schema declares none
 */
export const getSchemaRules = (formattedSchema) => {
  const rules = formattedSchema?.[SCHEMA_RULES];
  return Array.isArray(rules) ? rules : [];
};

export async function resolveDefaults(
  modelName,
  { throwOnError = false } = {},
) {
  try {
    const result = await getComponents({ model: modelName });
    const info = Array.isArray(result) ? result[0] : result;
    if (!info?.schema) return {};
    const formatted = await formattedModel(info.schema);
    const { initialValues } = generateYupSchema(formatted);
    return initialValues;
  } catch (e) {
    console.warn(`[resolveDefaults] Failed for ${modelName}:`, e);
    if (throwOnError) throw e;
    return {};
  }
}

/**
 * What an emptied input means for a given field.
 *
 * The problem this answers is old: a cleared text box hands back `""`, and for
 * a field like `group_column` an empty string is not "no value", it is a column
 * named "". sklearn then fails on it, or the backend stores it and a Huey worker
 * raises a KeyError much later. The historical patch went the other way, trying
 * to translate `""` to None during validation, and there was no good place for
 * it: the schema layer cannot tell, from a bare string, whether the author meant
 * "unset" or "the empty string".
 *
 * It can be derived instead, from what the schema already says on the wire:
 *
 *  - The field does not admit null: `""` is a value like any other, so it stays.
 *    A required field then reports itself empty, which is correct.
 *  - It admits null and its placeholder is `""`: the author chose the empty
 *    string as the default, so that is what empty means. This is the case of the
 *    14 `negative_prompt` fields across the diffusion models, and it is exactly
 *    why a single global rule would have been wrong.
 *  - It admits null and its placeholder is anything else: empty means unset.
 *
 * So there is no new keyword, no authoring burden and no backend change. The
 * answer was already in the schema; nobody was reading it.
 *
 * @param {object} subSchema one property of a formatted schema
 * @returns {null|string} the value an emptied input should submit
 */
export const emptyValueFor = (subSchema) => {
  const branches = Array.isArray(subSchema?.anyOf)
    ? subSchema.anyOf
    : [subSchema ?? {}];
  // If "" is one of the offered options it is a value, not emptiness. Plotly's
  // histnorm is the case: its empty string means raw counts.
  const emptyIsAnOption = branches.some(
    (branch) => Array.isArray(branch?.enum) && branch.enum.includes(""),
  );
  if (emptyIsAnOption) return "";
  const admitsNull =
    branches.some((branch) => branch?.type === "null") ||
    subSchema?.type === "null";
  if (!admitsNull) return "";
  return subSchema?.placeholder === "" ? "" : null;
};

/**
 * Replace an emptied input's value with what empty means for that field.
 *
 * Applied at the single point where a form reports a change, so every input
 * type is covered and no leaf component has to know about it.
 *
 * @param {*} value the value the input handed back
 * @param {object} subSchema the schema of the field that changed
 * @returns {*} the value to store
 */
export const normalizeEmptyValue = (value, subSchema) => {
  if (value !== "" && value !== undefined) return value;
  return emptyValueFor(subSchema);
};

// Generate a Yup schema from a JSON schema object based on the JSON schema specification from the api, it also generates the initial values of the form
export const generateYupSchema = (schemaObj) => {
  const schema = {};
  const initialValues = {};

  // Iterate over the properties of the schema object
  Object.keys(schemaObj).forEach((key) => {
    const subSchema = schemaObj[key];
    const field = generateField(subSchema);
    schema[key] = field;
    initialValues[key] = generateInitialValues(subSchema);
  });

  // withRules falls back to a plain object schema when there are no rules, so
  // every existing form keeps exactly the validation it had.
  return {
    schema: withRules(schema, getSchemaRules(schemaObj)),
    initialValues,
  };
};

export const generateInitialValues = (subSchema) => {
  let initialValues = {};

  // Special case for optimizable fields
  if (subSchema.placeholder?.optimize !== undefined) {
    initialValues = subSchema.placeholder;
  } else if (subSchema.type !== "object") {
    initialValues = subSchema.placeholder;
  } else if (subSchema.parent) {
    // If the object has a parent, we need to create the initial values accordingly
    initialValues = {
      properties: {
        component: subSchema.properties.component,
        params: {
          comp: {
            component: subSchema.properties.params.comp.component,
            params: Object.keys(subSchema.properties.params.comp.params).reduce(
              (acc, current) => {
                acc[current] = generateInitialValues(
                  subSchema.properties.params.comp.params[current],
                );
                return acc;
              },
              {},
            ),
          },
        },
      },
    };
  } else {
    initialValues = Object.keys(subSchema.properties).reduce((acc, current) => {
      acc[current] = generateInitialValues(subSchema.properties[current]);
      return acc;
    }, {});
  }
  return initialValues;
};

const generateField = (subSchema) => {
  let field;

  // SPECIAL CASE: If it has placeholder.optimize, it is an optimizable field
  // It must be validated as an object regardless of the declared type
  if (subSchema.placeholder?.optimize !== undefined) {
    // A parameter picked out of a set is searched over a subset of its
    // options, not an interval, so the envelope carries `choices` and the
    // numeric validators below would reject every one of its values.
    if (
      subSchema["x-dashai-search-dtype"] === "categorical" ||
      subSchema.placeholder?.choices !== undefined
    ) {
      // Same order of preference as the renderer, so what the control offers
      // and what passes validation are one list. The declared search space
      // comes first because it is the only place that names every option: a
      // field that also admits null keeps its `enum` inside an `anyOf` branch
      // that does not mention null, and a boolean has no `enum` at all.
      const options =
        subSchema.placeholder?.choices ??
        subSchema.enum ??
        subSchema.anyOf?.find((branch) => branch.enum !== undefined)?.enum;
      const option =
        options === undefined
          ? Yup.mixed().nullable()
          : Yup.mixed()
              .nullable()
              .oneOf([...options, null]);

      let categorical = Yup.object().shape({
        fixed_value: option,
        choices: Yup.array()
          .of(options === undefined ? Yup.mixed() : Yup.mixed().oneOf(options))
          .nullable(),
        optimize: Yup.boolean(),
      });

      categorical = categorical.test(
        "choices-validation",
        "A categorical search needs at least two distinct options",
        function (value) {
          if (!value?.optimize) return true;
          const choices = value.choices ?? [];
          return (
            choices.length >= 2 && new Set(choices).size === choices.length
          );
        },
      );

      return subSchema.required ? categorical.required() : categorical;
    }

    // Create base validators for optimizer fields with min/max constraints
    let fixedValueValidator = Yup.number().nullable();
    let lowerBoundValidator = Yup.number().nullable();
    let upperBoundValidator = Yup.number().nullable();

    // Apply min/max constraints from the schema to each field
    fixedValueValidator = applyMinMax(
      fixedValueValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    lowerBoundValidator = applyMinMax(
      lowerBoundValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    upperBoundValidator = applyMinMax(
      upperBoundValidator,
      subSchema.minimum,
      subSchema.maximum,
      subSchema.exclusiveMinimum,
      subSchema.exclusiveMaximum,
    );

    field = Yup.object()
      .shape({
        fixed_value: fixedValueValidator,
        lower_bound: lowerBoundValidator,
        upper_bound: upperBoundValidator,
        optimize: Yup.boolean(),
      })
      .test(
        "bounds-validation",
        "Lower bound must be less than or equal to upper bound",
        function (value) {
          if (!value) return true;
          const { lower_bound, upper_bound } = value;

          // Only validate if both bounds are defined
          if (lower_bound != null && upper_bound != null) {
            return lower_bound <= upper_bound;
          }
          return true;
        },
      );

    // Apply required validation if necessary
    if (subSchema.required) {
      field = field.required();
    }

    return field;
  }

  // For normal fields (non-optimizable)
  if (subSchema.anyOf) {
    field = Yup.mixed().nullable();
  } else if (subSchema.type === "object") {
    field = Yup.object();

    if (!subSchema.parent) {
      const properties = {};
      Object.keys(subSchema.properties).forEach((key) => {
        properties[key] = generateField(subSchema.properties[key]);
      });
      field = field.shape(properties);
    } else {
      field = getValidator(subSchema);
    }
  } else {
    field = getValidator(subSchema);
  }

  return field;
};

const getTypeValidator = (type) => {
  switch (type) {
    case "integer":
      return Yup.number().integer();
    case "number":
      return Yup.number();
    case "array":
      return Yup.array();
    case "string":
      return Yup.string();
    case "boolean":
      return Yup.boolean();
    case "null":
      return Yup.mixed().nullable();
    case "object":
      return Yup.object();
    default:
      throw new Error(`Unsupported type: ${type}`);
  }
};

const applyRequired = (validator, required) => {
  if (required) {
    return validator.required();
  }
  return validator;
};

const applyEnum = (validator, enumValues) => {
  if (enumValues) {
    return validator.oneOf(enumValues);
  }
  return validator;
};

const applyMinMax = (
  validator,
  minimum,
  maximum,
  exclusiveMinimum,
  exclusiveMaximum,
) => {
  if (minimum !== undefined) {
    validator = validator.min(minimum);
  }
  if (maximum !== undefined) {
    validator = validator.max(maximum);
  }
  if (exclusiveMinimum !== undefined) {
    validator = validator.min(exclusiveMinimum);
  }
  if (exclusiveMaximum !== undefined) {
    validator = validator.max(exclusiveMaximum);
  }
  return validator;
};

/**
 * Enforce the standard JSON Schema `multipleOf` keyword.
 *
 * Yup has no built-in for it, so it rides a test. Used by the diffusion models'
 * image sizes, which have to be multiples of 8 because the VAE downsamples by
 * that factor: the constraint used to live in the description in five languages
 * and nothing checked it, so a width of 513 reached the pipeline.
 *
 * @param {object} validator a Yup number validator
 * @param {number|undefined} multipleOf the required factor
 * @returns {object} the validator, with the constraint applied when there is one
 */
const applyMultipleOf = (validator, multipleOf) => {
  if (multipleOf === undefined || multipleOf === null) return validator;
  return validator.test(
    "multiple-of",
    `Must be a multiple of ${multipleOf}`,
    // An absent value is the required check's business, not this one's, and a
    // non-number is the type check's.
    (value) =>
      value === undefined ||
      value === null ||
      !Number.isFinite(Number(value)) ||
      Number(value) % multipleOf === 0,
  );
};

const applyArrayConstraints = (validator, itemSchema, minItems, maxItems) => {
  if (itemSchema) {
    validator = validator.of(itemSchema);
  }
  if (minItems !== undefined) {
    validator = validator.min(minItems);
  }
  if (maxItems !== undefined) {
    validator = validator.max(maxItems);
  }
  return validator;
};

// Generate a Yup validator from a JSON schema object
export const getValidator = (option) => {
  let validator;

  validator = getTypeValidator(option.type);
  if (option.type === "array" && option.items) {
    const itemValidator = getValidator(option.items);
    validator = applyArrayConstraints(
      validator,
      itemValidator,
      option.minItems,
      option.maxItems,
    );
  }
  validator = applyEnum(validator, option.enum);
  validator = applyMinMax(
    validator,
    option.minimum,
    option.maximum,
    option.exclusiveMinimum,
    option.exclusiveMaximum,
  );
  validator = applyMultipleOf(validator, option.multipleOf);
  validator = applyRequired(validator, option.required);

  return validator;
};

// Format the model schema to include the subforms
export const formattedModel = async (schema) => {
  const subforms = {};
  const required = schema.required || [];

  await Promise.all(
    Object.keys(schema.properties)
      .filter((key) => {
        return (
          schema.properties[key].type === "object" &&
          schema.properties[key].parent
        );
      })
      .map(async (key) => {
        const obj = schema.properties[key];

        const subform = await getComponents({
          model: obj.placeholder.component,
        });

        subforms[key] = {
          properties: {
            component: obj.parent,
            params: {
              comp: {
                component: obj.placeholder.component,
                params: await formattedModel(subform.schema),
              },
            },
          },
          type: "object",
          description: obj.description,
          title: obj.title,
          parent: obj.parent,
        };
      }),
  );

  const formattedSchema = { ...schema.properties, ...subforms };

  // Add required property to each key-value pair in the formattedSchema object
  Object.keys(formattedSchema).forEach((key) => {
    formattedSchema[key] = {
      ...formattedSchema[key],
      required: required.includes(key),
    };
  });

  // This function flattens the schema down to its properties, which is where
  // the root-level rule set would otherwise be dropped. Carry it on a symbol
  // so it survives without becoming a fourteenth field to render.
  formattedSchema[SCHEMA_RULES] = Array.isArray(schema["x-dashai-rules"])
    ? schema["x-dashai-rules"]
    : [];

  return formattedSchema;
};

// Format the subform schema to include the parent model
export const formattedSubform = ({ parent, model, params }) => ({
  properties: {
    component: parent,
    params: {
      comp: {
        component: model,
        params,
      },
    },
  },
});

export const checkIfHaveOptimazers = (values) => {
  if (!values) return false;

  for (const key of Object.keys(values)) {
    const param = values[key];
    if (!param || typeof param !== "object") continue;

    if (param.optimize) {
      return true;
    }

    // Only return true if a recursive check finds something
    if (checkIfHaveOptimazers(param)) {
      return true;
    }
  }

  return false;
};

export const checkHowManyOptimazers = (values) => {
  let count = 0;

  if (!values) return count;

  for (const key of Object.keys(values)) {
    const param = values[key];
    if (!param || typeof param !== "object") continue;

    if (param.optimize) {
      count += 1;
    }

    // Recursively count optimizers in nested objects
    count += checkHowManyOptimazers(param);
  }

  return count;
};

export const getParamsFromSubform = (subform) => {
  if (!subform) {
    return null;
  }
  if (subform.properties?.params?.comp?.params) {
    return subform.properties.params.comp.params;
  }
  if (subform.params !== undefined) {
    return subform.params;
  }
  return subform.properties?.params ?? null;
};

export const getModelFromSubform = (subform) => {
  if (!subform) {
    return null;
  }
  if (subform.component !== undefined) {
    return subform.component;
  }
  if (subform.properties?.params?.comp?.component) {
    return subform.properties.params.comp.component;
  }
  return subform.properties?.component ?? null;
};
