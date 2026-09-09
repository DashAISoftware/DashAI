import { ToggleButton, ToggleButtonGroup } from "@mui/material";
import React from "react";
import PropTypes from "prop-types";

/**
 * This component is a single select toggle group — the options are rendered
 * as one connected control (not separate buttons) so it reads as a switch
 * between mutually exclusive choices, e.g. "Int" vs "Null" for a nullable
 * field's type.
 * @param {Array} options - The options to display
 * @param {function} onChange - The function to update the selected option
 * @param {string} selected - The selected option
 * @param {boolean} disabled - Renders the whole group inert, for a field a
 *   relevance rule has switched off: the type must not be changeable either,
 *   or switching it would write a value into a field that means nothing.
 */

const SingleSelectChipGroup = ({
  options,
  onChange,
  selected,
  disabled = false,
}) => {
  const handleChange = (event, value) => {
    if (value !== null) onChange(value);
  };

  return (
    <ToggleButtonGroup
      value={selected}
      exclusive
      onChange={handleChange}
      size="small"
      disabled={disabled}
      aria-label="type selector"
      sx={{ borderRadius: 1 }}
    >
      {options.map((option, index) => (
        <ToggleButton
          key={"option-" + option.key + "-" + index}
          value={option.key}
          sx={{
            textTransform: "none",
            px: 3,
            border: "1px solid transparent",
            color: "text.secondary",
            bgcolor: "ui.box",
            // Same "current state, not an action" treatment as the app's
            // tab-style toggles (PillToggleButtonGroup) — a solid fill here
            // read too much like the primary action buttons elsewhere.
            "&.Mui-selected": {
              bgcolor: "background.paper",
              color: "primary.main",
              fontWeight: 600,
              borderBottom: "2px solid",
              borderBottomColor: "primary.main",
              "&:hover": { bgcolor: "background.paper" },
            },
          }}
        >
          {option.label}
        </ToggleButton>
      ))}
    </ToggleButtonGroup>
  );
};

SingleSelectChipGroup.propTypes = {
  options: PropTypes.array.isRequired,
  onChange: PropTypes.func.isRequired,
  selected: PropTypes.string.isRequired,
  disabled: PropTypes.bool,
};

export default SingleSelectChipGroup;
