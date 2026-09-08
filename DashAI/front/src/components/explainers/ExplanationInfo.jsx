import React from "react";
import PropTypes from "prop-types";
import { Box, Chip, Stack, Typography } from "@mui/material";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import { useTranslation } from "react-i18next";

import { formatColumnAtom } from "../../utils/columnAtoms";

/**
 * Read only summary of the model's input and target columns, shown while
 * choosing the data to explain so the user knows which features feed the model.
 *
 * `outputColumns` comes straight off the model session, so its entries are
 * column *atoms* (`{kind: "column", name}` / `{kind: "group", converter_id,
 * slot}`), not plain names — rendering one directly into a `<Chip label>`
 * crashed React with "Objects are not valid as a React child". Every entry
 * is therefore run through `formatColumnAtom`, which also passes plain
 * strings (what `inputColumns` still is: raw training-dataset column names,
 * see SelectDatasetStep) through untouched. `converters` is the session's
 * own converter list, needed only to name a `group` atom's source converter.
 */
export default function ExplanationInfo({
  inputColumns,
  outputColumns,
  converters = [],
}) {
  const { t } = useTranslation(["explainers", "common"]);

  const format = (col) =>
    formatColumnAtom(col, { converters, unknownLabel: t("common:unknown") });

  if (
    (!inputColumns || inputColumns.length === 0) &&
    (!outputColumns || outputColumns.length === 0)
  ) {
    return null;
  }

  return (
    <Box
      sx={{
        p: 4,
        borderRadius: 2,
        border: 1,
        borderColor: "primary.main",
        bgcolor: (theme) => `${theme.palette.primary.main}14`,
      }}
    >
      <Stack direction="row" alignItems="center" spacing={2} sx={{ mb: 3 }}>
        <InfoOutlinedIcon color="primary" fontSize="small" />
        <Typography variant="subtitle2" color="primary">
          {t("explainers:label.explanationInfo")}
        </Typography>
      </Stack>

      <Typography variant="caption" fontWeight={600} display="block">
        {t("explainers:label.inputColumns")}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1, mb: 3 }}>
        {(inputColumns ?? []).map((col, index) => (
          <Chip
            key={`${format(col)}-${index}`}
            label={format(col)}
            size="small"
            variant="outlined"
          />
        ))}
      </Box>

      <Typography variant="caption" fontWeight={600} display="block">
        {t("explainers:label.targetColumn")}
      </Typography>
      <Box sx={{ display: "flex", flexWrap: "wrap", gap: 1, mt: 1 }}>
        {(outputColumns ?? []).map((col, index) => (
          <Chip
            key={`${format(col)}-${index}`}
            label={format(col)}
            size="small"
            color="primary"
          />
        ))}
      </Box>
    </Box>
  );
}

const columnAtomPropType = PropTypes.oneOfType([
  PropTypes.string,
  PropTypes.object,
]);

ExplanationInfo.propTypes = {
  inputColumns: PropTypes.arrayOf(columnAtomPropType),
  outputColumns: PropTypes.arrayOf(columnAtomPropType),
  converters: PropTypes.array,
};
