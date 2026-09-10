import { memo, useState } from "react";
import PropTypes from "prop-types";
import { Chip, Menu, MenuItem, Tooltip } from "@mui/material";
import { useTranslation } from "react-i18next";

const ENCODER_OPTIONS = ["one_hot", "label"];

/**
 * Presentational encoder chip + dropdown menu. Self-contained anchor state
 * so toggling the menu does not re-render sibling components.
 *
 * Callers supply ``onSelect(encoder)`` and optionally an ``encoderLabel``
 * function for custom display text.
 */
const EncoderChipBase = memo(function EncoderChipBase({
  encoder,
  onSelect,
  disabled = false,
  encoderLabel,
}) {
  const [anchor, setAnchor] = useState(null);
  const { t } = useTranslation(["common"]);

  const label = encoderLabel ? encoderLabel(encoder) : (encoder ?? "-");

  return (
    <>
      <Tooltip title={t("common:changeEncoder")} arrow>
        <span style={{ display: "inline-flex" }}>
          <Chip
            label={label}
            size="small"
            disabled={disabled}
            onClick={(e) => {
              e.stopPropagation();
              setAnchor(e.currentTarget);
            }}
            aria-label={t("common:encoder")}
            sx={{
              fontSize: "0.65rem",
              height: "18px",
              cursor: disabled ? "default" : "pointer",
            }}
          />
        </span>
      </Tooltip>
      {anchor && (
        <Menu
          anchorEl={anchor}
          open={Boolean(anchor)}
          onClose={() => setAnchor(null)}
        >
          {ENCODER_OPTIONS.map((opt) => (
            <MenuItem
              key={opt}
              selected={opt === encoder}
              onClick={() => {
                setAnchor(null);
                onSelect(opt);
              }}
              sx={{ fontSize: "0.85rem" }}
            >
              {encoderLabel ? encoderLabel(opt) : opt}
            </MenuItem>
          ))}
        </Menu>
      )}
    </>
  );
});

EncoderChipBase.propTypes = {
  encoder: PropTypes.string,
  onSelect: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
  encoderLabel: PropTypes.func,
};

export default EncoderChipBase;
