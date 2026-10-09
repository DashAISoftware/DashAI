import React from "react";
import PropTypes from "prop-types";
import {
  Box,
  Checkbox,
  FormControl,
  FormControlLabel,
  FormHelperText,
  Switch,
} from "@mui/material";
import FormInputWrapper from "./FormInputWrapper";
import { useFormCard } from "../../../contexts/FormCardContext";

/**
 * Renders a boolean input.
 * Inside a card the label is already shown in the card header, so only a compact
 * Switch is rendered (same height as size="small" TextFields).
 * Outside a card the full Checkbox + label layout is used.
 */
function BooleanInput({
  name,
  value,
  label,
  onChange,
  error,
  description,
  disabled = false,
}) {
  const isInCard = useFormCard();

  if (isInCard) {
    return (
      <Box
        sx={{
          display: "flex",
          alignItems: "center",
          height: 36, // match size="small" TextField height
        }}
      >
        <FormControl error={error !== undefined} disabled={disabled}>
          <Switch
            size="small"
            disabled={disabled}
            name={name}
            checked={Boolean(value)}
            onChange={(e) => onChange(e.target.checked)}
          />
          {error && <FormHelperText sx={{ mt: 0 }}>{error}</FormHelperText>}
        </FormControl>
      </Box>
    );
  }

  return (
    <FormInputWrapper name={name} description={description} disabledPadding>
      <FormControl error={error !== undefined}>
        <FormControlLabel
          label={label}
          control={
            <Checkbox
              disabled={disabled}
              name={name}
              checked={Boolean(value)}
              onChange={(e) => onChange(e.target.checked)}
            />
          }
        />
        {error && <FormHelperText>{error}</FormHelperText>}
      </FormControl>
    </FormInputWrapper>
  );
}

BooleanInput.propTypes = {
  name: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
  value: PropTypes.bool,
  label: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
  description: PropTypes.string.isRequired,
  error: PropTypes.string,
};

export default BooleanInput;
