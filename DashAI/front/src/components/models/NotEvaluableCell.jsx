import PropTypes from "prop-types";
import { Box, Chip, TableCell, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";

/**
 * Table cell shown in place of a row's p-value and decision when the test
 * could not be computed for that row (e.g. a run with constant scores, or a
 * pair of models whose difference is the same on every fold).
 *
 * @param {object} props
 * @param {string} [props.error]  Short reason returned by the backend.
 * @param {number} [props.colSpan]  Number of result columns it replaces.
 */
function NotEvaluableCell({ error, colSpan = 1 }) {
  const { t } = useTranslation(["models"]);

  return (
    <TableCell colSpan={colSpan}>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Chip
          label={t("models:label.notEvaluable")}
          color="warning"
          size="small"
          variant="outlined"
          sx={{ flexShrink: 0 }}
        />
        {error && (
          <Typography variant="caption" color="text.secondary">
            {error}
          </Typography>
        )}
      </Box>
    </TableCell>
  );
}

NotEvaluableCell.propTypes = {
  error: PropTypes.string,
  colSpan: PropTypes.number,
};

export default NotEvaluableCell;
