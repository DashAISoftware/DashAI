import PropTypes from "prop-types";
import React from "react";
import { FormControlLabel, Switch, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import OptimizeIntegerInput from "../configurableObject/Inputs/IntegerInputOptimize";
import OptimizeNumberInput from "../configurableObject/Inputs/NumberInputOptimize";
import OptimizeSelectInput from "../configurableObject/Inputs/SelectInputOptimize";
import FormSchemaFieldCard from "./FormSchemaFieldCard";

/**
 * Renders an optimizable field inside a FormSchemaFieldCard.
 *
 * The optimize toggle lives in the card header; the input body shows the fixed
 * value or the search space depending on the switch state. What a search space
 * looks like depends on the kind of parameter: an interval for something
 * measured on a scale, a subset of the options for something picked out of a
 * set.
 */
function FormSchemaFieldWithOptimizers({ objName, paramJsonSchema, field }) {
  const { type } = paramJsonSchema;
  const { t } = useTranslation(["common"]);

  const canOptimize = paramJsonSchema?.placeholder?.optimize !== undefined;

  // Declared by the backend rather than inferred from the JSON Schema `type`,
  // which is absent whenever a field also admits null and cannot say
  // "categorical" at all. The `type` fallback covers the fields still declared
  // as an `optimizer_*_field` with a hand-written placeholder.
  const searchDtype =
    paramJsonSchema?.["x-dashai-search-dtype"] ??
    (type === "integer" ? "integer" : "number");
  const isCategorical = searchDtype === "categorical";

  // The declared search space is what the control offers, because it is the
  // only place that lists every option: `enum` sits one level down inside the
  // `anyOf` branch of a field that also admits null and does not mention null
  // itself, and a boolean has no `enum` at all. Offering `enum` here meant a
  // user who unticked "None" on `class_weight` could not tick it back.
  const options =
    paramJsonSchema?.placeholder?.choices ??
    paramJsonSchema?.enum ??
    paramJsonSchema?.anyOf?.find((branch) => branch.enum !== undefined)?.enum ??
    [];

  // `enumNames` is aligned with `enum`, which is not necessarily aligned with
  // the options above, so the names are matched by option rather than by
  // index. An option with no name of its own falls back to the label the input
  // gives it, which is how null and the two booleans get theirs.
  const named =
    paramJsonSchema?.enum !== undefined
      ? paramJsonSchema
      : (paramJsonSchema?.anyOf?.find(
          (branch) => branch.enumNames !== undefined,
        ) ?? {});
  const optionNames =
    named.enumNames === undefined
      ? undefined
      : options.map(
          (option) => named.enumNames[named.enum.indexOf(option)] ?? undefined,
        );

  // Derived directly from field.value rather than mirrored into local state —
  // a local copy synced via useEffect lags the real value by a render, which
  // briefly flashed the wrong mode (fixed-value defaults instead of the
  // saved range) whenever this field remounted with a fresh value.
  const switchState =
    field?.value?.optimize ?? paramJsonSchema?.placeholder?.optimize ?? false;

  const handleSwitchChange = () => {
    const toggled = !switchState;
    const placeholder = paramJsonSchema?.placeholder;
    const hasError = field?.error !== undefined;
    const pick = (key, fallback) =>
      hasError
        ? (placeholder?.[key] ?? fallback)
        : (field?.value?.[key] ?? placeholder?.[key] ?? fallback);
    // Only the keys belonging to this kind of space are sent. The envelope
    // rejects an interval and a set of choices at the same time, so carrying
    // both would make every categorical parameter invalid the moment its
    // toggle was touched.
    field.onChange({
      fixed_value: hasError
        ? (placeholder?.fixed_value ?? null)
        : (field?.value?.fixed_value ?? null),
      ...(isCategorical
        ? { choices: pick("choices", options) }
        : {
            lower_bound: hasError
              ? (placeholder?.lower_bound ?? null)
              : (field?.value?.lower_bound ?? null),
            upper_bound: hasError
              ? (placeholder?.upper_bound ?? null)
              : (field?.value?.upper_bound ?? null),
          }),
      optimize: toggled,
    });
  };

  const optimizeToggle = canOptimize ? (
    <FormControlLabel
      label={
        <Typography variant="caption" color="text.secondary">
          {t("common:optimize")}
        </Typography>
      }
      labelPlacement="start"
      control={
        <Switch
          size="small"
          checked={switchState}
          onChange={handleSwitchChange}
        />
      }
      sx={{ mr: 0, gap: 1 }}
    />
  ) : null;

  const commonProps = {
    name: objName,
    value: field?.value,
    label: paramJsonSchema.title,
    onChange: field?.onChange,
    error: field?.error || undefined,
    description: paramJsonSchema?.description,
    placeholder: paramJsonSchema?.placeholder,
    externalSwitchState: switchState,
  };

  return (
    <FormSchemaFieldCard
      label={paramJsonSchema.title}
      paramKey={objName}
      description={paramJsonSchema?.description}
      headerRight={optimizeToggle}
    >
      {isCategorical ? (
        <OptimizeSelectInput
          {...commonProps}
          options={options}
          optionNames={optionNames}
        />
      ) : searchDtype === "integer" ? (
        <OptimizeIntegerInput {...commonProps} />
      ) : (
        <OptimizeNumberInput {...commonProps} />
      )}
    </FormSchemaFieldCard>
  );
}

FormSchemaFieldWithOptimizers.propTypes = {
  objName: PropTypes.string,
  paramJsonSchema: PropTypes.object,
  field: PropTypes.object,
};

export default FormSchemaFieldWithOptimizers;
