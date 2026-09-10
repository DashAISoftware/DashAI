import PropTypes from "prop-types";
import {
  Box,
  Button,
  Checkbox,
  FormControlLabel,
  Menu,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";

export default function LeanColumnsMenu({
  anchor,
  allColumnKeys,
  hiddenColumns,
  onClose,
  onToggleColumn,
  onShowAll,
  onHideAll,
}) {
  const { t } = useTranslation(["datasets"]);
  return (
    <Menu
      anchorEl={anchor}
      open={Boolean(anchor)}
      onClose={onClose}
      slotProps={{ paper: { sx: { maxHeight: 400, minWidth: 220 } } }}
    >
      <Box sx={{ px: 2, pt: 1, pb: 1, display: "flex", gap: 2 }}>
        <Button size="small" onClick={onShowAll}>
          {t("datasets:table.showAll")}
        </Button>
        <Button size="small" onClick={onHideAll}>
          {t("datasets:table.hideAll")}
        </Button>
      </Box>
      <Box sx={{ px: 2, pb: 1 }}>
        {allColumnKeys.map((key) => (
          <FormControlLabel
            key={key}
            control={
              <Checkbox
                size="small"
                checked={!hiddenColumns.has(key)}
                onChange={() => onToggleColumn(key)}
              />
            }
            label={
              <Typography variant="body2" sx={{ fontSize: 13 }}>
                {key}
              </Typography>
            }
            sx={{ display: "flex", m: 0 }}
          />
        ))}
      </Box>
    </Menu>
  );
}

LeanColumnsMenu.propTypes = {
  anchor: PropTypes.any,
  allColumnKeys: PropTypes.arrayOf(PropTypes.string).isRequired,
  hiddenColumns: PropTypes.instanceOf(Set).isRequired,
  onClose: PropTypes.func.isRequired,
  onToggleColumn: PropTypes.func.isRequired,
  onShowAll: PropTypes.func.isRequired,
  onHideAll: PropTypes.func.isRequired,
};
