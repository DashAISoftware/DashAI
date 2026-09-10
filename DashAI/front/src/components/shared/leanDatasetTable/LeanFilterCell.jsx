import { memo, useState } from "react";
import PropTypes from "prop-types";
import { Box, Menu, MenuItem } from "@mui/material";
import { useTranslation } from "react-i18next";

import { NUMERIC_TYPES, opsByType } from "./operators";

const LeanFilterCell = memo(function LeanFilterCell({
  columnKey,
  type,
  operator,
  value,
  isPinned,
  pinnedOffset,
  onOperatorChange,
  onValueChange,
}) {
  const [anchor, setAnchor] = useState(null);
  const { t } = useTranslation(["datasets"]);

  const ops = opsByType(type);
  const currentOp = ops.find((o) => o.value === operator) ?? ops[0];
  const isNumeric = NUMERIC_TYPES.has(type);
  const isEmptyOp = operator === "empty" || operator === "notEmpty";
  const isBetween = operator === "between";
  const inputType = isNumeric ? "number" : "text";
  const v1 = Array.isArray(value) ? (value[0] ?? "") : (value ?? "");
  const v2 = Array.isArray(value) ? (value[1] ?? "") : "";

  const opLabel = (op) => t(`datasets:table.op.${op}`, { defaultValue: op });

  return (
    <th
      className={
        isPinned ? "lean-th-filter lean-th-filter--pinned" : "lean-th-filter"
      }
      style={isPinned ? { right: pinnedOffset ?? 0 } : undefined}
    >
      <div className="lean-filter-cell">
        <button
          type="button"
          className="lean-op-btn"
          title={opLabel(currentOp.value)}
          onClick={(e) => {
            e.stopPropagation();
            setAnchor(e.currentTarget);
          }}
        >
          {currentOp.symbol}
        </button>
        {isEmptyOp ? (
          <div className="lean-filter-placeholder" />
        ) : isBetween ? (
          <>
            <input
              className="lean-filter-input lean-filter-input--half"
              type={inputType}
              placeholder={t("datasets:table.filterMin")}
              value={v1}
              onChange={(e) => onValueChange([e.target.value, v2])}
            />
            <input
              className="lean-filter-input lean-filter-input--half"
              type={inputType}
              placeholder={t("datasets:table.filterMax")}
              value={v2}
              onChange={(e) => onValueChange([v1, e.target.value])}
            />
          </>
        ) : (
          <input
            className="lean-filter-input"
            type={inputType}
            placeholder={opLabel(currentOp.value).toLowerCase()}
            value={v1}
            onChange={(e) => onValueChange(e.target.value)}
          />
        )}
      </div>
      {anchor && (
        <Menu
          anchorEl={anchor}
          open={Boolean(anchor)}
          onClose={() => setAnchor(null)}
          slotProps={{ paper: { sx: { minWidth: 220 } } }}
        >
          {ops.map((op) => (
            <MenuItem
              key={op.value}
              selected={op.value === operator}
              onClick={() => {
                setAnchor(null);
                if (op.value !== operator) onOperatorChange(op.value);
              }}
              dense
              sx={{ fontSize: 13 }}
            >
              <Box
                sx={{
                  display: "flex",
                  alignItems: "center",
                  gap: 1.5,
                  width: "100%",
                }}
              >
                <Box
                  sx={{
                    minWidth: 18,
                    textAlign: "center",
                    opacity: 0.7,
                    fontFamily: "monospace",
                  }}
                >
                  {op.symbol}
                </Box>
                {opLabel(op.value)}
              </Box>
            </MenuItem>
          ))}
        </Menu>
      )}
    </th>
  );
});

LeanFilterCell.propTypes = {
  columnKey: PropTypes.string.isRequired,
  type: PropTypes.string,
  operator: PropTypes.string.isRequired,
  value: PropTypes.any,
  isPinned: PropTypes.bool,
  pinnedOffset: PropTypes.number,
  onOperatorChange: PropTypes.func.isRequired,
  onValueChange: PropTypes.func.isRequired,
};

export default LeanFilterCell;
