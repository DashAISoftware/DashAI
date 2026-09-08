import React, { useState, useEffect } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Checkbox,
  Chip,
  FormControl,
  FormControlLabel,
  ListItemText,
  MenuItem,
  Switch,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import FormInputWrapper from "./FormInputWrapper";
import { Input } from "./InputStyles";

/**
 * Renders an HPO form field for parameters chosen out of a set: an enum, or a
 * boolean.
 *
 * The numeric inputs ask for a lower and an upper bound, which is the only
 * shape the optimizer form has ever had. That shape cannot describe this kind
 * of parameter at all: `hinge` is not between `squared_hinge` and anything
 * else, so a search over it is a subset of the options rather than an
 * interval. When the toggle is on this shows which options are in play; when
 * it is off it is an ordinary dropdown for the fixed value.
 *
 * Option labels come from `optionNames`, which the backend emits as
 * `enumNames` alongside `enum`, so the list reads "Log loss" rather than
 * `log_loss`.
 */
function OptimizeSelectInput({
  name,
  label,
  value = {},
  onChange,
  description = "",
  error = undefined,
  placeholder = {},
  options,
  optionNames = undefined,
  externalSwitchState,
}) {
  const { t } = useTranslation("configurableObject");

  const mergedOptimize = value?.optimize ?? placeholder?.optimize ?? false;
  const mergedFixed = value?.fixed_value ?? placeholder?.fixed_value ?? null;
  const mergedChoices = value?.choices ?? placeholder?.choices ?? options ?? [];

  const [internalSwitchState, setInternalSwitchState] =
    useState(mergedOptimize);

  const isExternallyControlled = externalSwitchState !== undefined;
  const switchState = isExternallyControlled
    ? externalSwitchState
    : internalSwitchState;

  useEffect(() => {
    if (!isExternallyControlled) {
      setInternalSwitchState(mergedOptimize);
    }
  }, [mergedOptimize, isExternallyControlled]);

  const fieldError = (field) =>
    error === undefined
      ? null
      : typeof error === "string"
        ? error
        : error[field] || null;

  const fixedError = !switchState ? fieldError("fixed_value") : null;
  const choicesError = switchState ? fieldError("choices") : null;

  // A boolean has no `enum` to name its two values, so they are named here.
  const nameOf = (option, index) => {
    if (optionNames !== undefined && optionNames[index] !== undefined) {
      return optionNames[index];
    }
    if (typeof option === "boolean") {
      return t(option ? "optionTrue" : "optionFalse");
    }
    if (option === null) {
      return t("optionNone");
    }
    return String(option);
  };

  const handleSwitchChange = () => {
    if (isExternallyControlled) return;
    const toggled = !internalSwitchState;
    setInternalSwitchState(toggled);
    onChange({
      fixed_value: mergedFixed,
      choices: mergedChoices,
      optimize: toggled,
    });
  };

  const handleChangeFixed = (event) => {
    onChange({ ...value, fixed_value: event.target.value });
  };

  const handleChangeChoices = (event) => {
    // MUI hands back the selected values in menu order, which is the order the
    // options were declared in, so the list stays stable as boxes are ticked.
    onChange({ ...value, choices: event.target.value });
  };

  const canOptimize = placeholder?.optimize !== undefined;

  return (
    <FormInputWrapper name={name} description={description}>
      {canOptimize && !isExternallyControlled && (
        <FormControl>
          <FormControlLabel
            label={t("optimize", { name: label || name })}
            control={
              <Switch
                name={name}
                checked={switchState}
                onChange={handleSwitchChange}
              />
            }
          />
        </FormControl>
      )}
      {canOptimize && switchState ? (
        <Box>
          <Typography
            variant="caption"
            color="text.secondary"
            sx={{ mb: 1, display: "block" }}
          >
            {t("searchedOptions")}
          </Typography>
          <Input
            select
            size="small"
            name={`${name}-choices`}
            value={mergedChoices}
            onChange={handleChangeChoices}
            error={choicesError !== null}
            helperText={choicesError ?? t("atLeastTwoOptions")}
            sx={{ width: "100%" }}
            slotProps={{
              select: {
                multiple: true,
                renderValue: (selected) => (
                  <Box sx={{ display: "flex", flexWrap: "wrap", gap: 0.5 }}>
                    {selected.map((option) => (
                      <Chip
                        key={String(option)}
                        size="small"
                        label={nameOf(option, options.indexOf(option))}
                      />
                    ))}
                  </Box>
                ),
              },
            }}
          >
            {options.map((option, index) => (
              <MenuItem key={String(option)} value={option}>
                <Checkbox
                  size="small"
                  checked={mergedChoices.includes(option)}
                  sx={{ py: 0 }}
                />
                <ListItemText primary={nameOf(option, index)} />
              </MenuItem>
            ))}
          </Input>
        </Box>
      ) : (
        <Input
          select
          size="small"
          label={label || t("enterValue")}
          name={`${name}-fixed`}
          value={mergedFixed !== null ? mergedFixed : ""}
          onChange={handleChangeFixed}
          error={fixedError !== null}
          helperText={fixedError}
          sx={{ width: "100%" }}
        >
          {options.map((option, index) => (
            <MenuItem key={String(option)} value={option}>
              <ListItemText primary={nameOf(option, index)} />
            </MenuItem>
          ))}
        </Input>
      )}
    </FormInputWrapper>
  );
}

OptimizeSelectInput.propTypes = {
  name: PropTypes.string,
  label: PropTypes.string,
  description: PropTypes.string,
  value: PropTypes.shape({
    optimize: PropTypes.bool,
    fixed_value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
    choices: PropTypes.array,
  }),
  onChange: PropTypes.func.isRequired,
  placeholder: PropTypes.shape({
    optimize: PropTypes.bool,
    fixed_value: PropTypes.oneOfType([PropTypes.string, PropTypes.bool]),
    choices: PropTypes.array,
  }),
  options: PropTypes.array.isRequired,
  optionNames: PropTypes.arrayOf(PropTypes.string),
  error: PropTypes.oneOfType([PropTypes.string, PropTypes.object]),
  externalSwitchState: PropTypes.bool,
};

export default OptimizeSelectInput;
