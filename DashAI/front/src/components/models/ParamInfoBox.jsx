import React, { useState } from "react";
import PropTypes from "prop-types";
import { Box, Collapse, Paper, Typography } from "@mui/material";
import { ExpandLess, ExpandMore } from "@mui/icons-material";

// Unwrap properties wrappers and single-entry model params to reach the leaf model.
// e.g. {properties: {component: "TaskModel", params: {comp: {component: "SVC", params: {...}}}}}
// → {component: "SVC", params: {...}}
function unwrapToLeafModel(value) {
  if (typeof value !== "object" || value === null) return value;
  if ("properties" in value) return unwrapToLeafModel(value.properties);
  if ("component" in value && "params" in value) {
    const entries = Object.entries(value.params);
    if (entries.length === 1) {
      const inner = entries[0][1];
      if (
        typeof inner === "object" &&
        inner !== null &&
        "component" in inner &&
        "params" in inner
      ) {
        return unwrapToLeafModel(inner);
      }
    }
  }
  return value;
}

function asNestedComponent(value) {
  if (typeof value !== "object" || value === null) return null;
  if ("fixed_value" in value) return null;
  const unwrapped = unwrapToLeafModel(value);
  if (
    unwrapped &&
    typeof unwrapped === "object" &&
    "component" in unwrapped &&
    "params" in unwrapped
  ) {
    return unwrapped;
  }
  return null;
}

function formatLeafValue(value) {
  if (typeof value !== "object" || value === null) return String(value);
  if ("fixed_value" in value) return String(value.fixed_value);
  return JSON.stringify(value);
}

/**
 * One parameter as its own small card - same shell as the editable
 * parameter cards used when configuring a model (bordered, rounded, bold
 * label in a header row), just more compact since there's no input/toggle
 * to fit, and read-only. The label sits on its own header row, never on
 * the same line as the value, so long labels/values never compete for
 * horizontal space.
 *
 * When the value is itself a nested component (a classifier plugged into
 * another model, an optimizer's own sub-parameters, etc.) the header
 * becomes clickable and collapses/expands that component's own parameters,
 * each rendered as this same card - so a parameter nested arbitrarily many
 * levels deep still renders (and collapses) correctly, not just one level.
 */
export function ParamInfoBox({ label, value }) {
  const [open, setOpen] = useState(false);
  const nested = asNestedComponent(value);

  return (
    <Paper variant="outlined" sx={{ borderRadius: 2, overflow: "hidden" }}>
      <Box
        onClick={nested ? () => setOpen((v) => !v) : undefined}
        sx={{
          px: 3,
          py: 1.5,
          display: "flex",
          alignItems: "center",
          gap: 2,
          borderBottom: !nested || open ? "1px solid" : "none",
          borderColor: "divider",
          cursor: nested ? "pointer" : "default",
          userSelect: nested ? "none" : "auto",
          "&:hover": nested ? { bgcolor: "action.hover" } : undefined,
        }}
      >
        <Typography
          variant="body2"
          fontWeight={600}
          sx={{ flex: 1, minWidth: 0 }}
        >
          {label}
        </Typography>
        {nested && (
          <>
            <Typography variant="caption" color="text.secondary">
              {nested.component}
            </Typography>
            {open ? (
              <ExpandLess sx={{ fontSize: 18 }} />
            ) : (
              <ExpandMore sx={{ fontSize: 18 }} />
            )}
          </>
        )}
      </Box>

      {nested ? (
        <Collapse in={open}>
          <Box sx={{ display: "flex", flexDirection: "column", gap: 2, p: 3 }}>
            {Object.entries(nested.params).map(([key, val]) => (
              <ParamInfoBox key={key} label={key} value={val} />
            ))}
          </Box>
        </Collapse>
      ) : (
        <Box sx={{ px: 3, pb: 1.5 }}>
          <Typography variant="body2" color="text.secondary">
            {formatLeafValue(value)}
          </Typography>
        </Box>
      )}
    </Paper>
  );
}

ParamInfoBox.propTypes = {
  label: PropTypes.node.isRequired,
  value: PropTypes.any,
};

/** Stacked list of ParamInfoBox, one per [label, value] pair. */
export default function ParamInfoList({ rows }) {
  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
      {rows.map(([label, value]) => (
        <ParamInfoBox key={label} label={label} value={value} />
      ))}
    </Box>
  );
}

ParamInfoList.propTypes = {
  rows: PropTypes.arrayOf(PropTypes.array).isRequired,
};
