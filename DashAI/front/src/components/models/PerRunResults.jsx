import { forwardRef } from "react";
import PropTypes from "prop-types";
import {
  Box,
  Typography,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { formatPValue } from "../../utils/statisticalTests";
import TechnicalDetails from "./TechnicalDetails";

/**
 * Renders the results of a per-run test, where the same test is applied
 * independently to each selected run (e.g. Shapiro-Wilk normality).
 *
 * Note on semantics: for normality tests, `significant === true` means the
 * null hypothesis of normality is rejected, i.e. the data is NOT normal.
 *
 * @param {object} props
 * @param {Array<{id:(number|string), name:string, resp:object}>} props.results
 *        One entry per run, each carrying its StatisticalTestResponse in `resp`.
 * @param {string} [props.title]  Heading (usually the test display name).
 */
const PerRunResults = forwardRef(function PerRunResults(
  { results, title },
  ref,
) {
  const { t } = useTranslation(["models", "common"]);

  if (!results || results.length === 0) return null;

  const normalCount = results.filter((r) => !r.resp.significant).length;
  const effectiveAlpha = results[0]?.resp?.alpha;

  return (
    <Box
      ref={ref}
      sx={{
        mt: 3,
        pt: 2,
        borderTop: "1px solid",
        borderColor: "divider",
      }}
    >
      {title && (
        <Typography variant="h6" sx={{ mb: 1.5 }}>
          {title}
        </Typography>
      )}

      <Alert severity="info" sx={{ mb: 2 }}>
        {t("models:label.normalityByRunSummary", {
          normal: normalCount,
          total: results.length,
          alpha: effectiveAlpha,
        })}
      </Alert>

      <Table size="small">
        <TableHead>
          <TableRow>
            <TableCell>Run</TableCell>
            <TableCell align="right">{t("models:label.statistic")}</TableCell>
            <TableCell align="right">p-value</TableCell>
            <TableCell align="center">{t("models:label.result")}</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {results.map(({ id, name, resp }) => {
            const hasStatistic =
              resp.statistic !== null && !isNaN(resp.statistic);
            return (
              <TableRow key={id}>
                <TableCell>{name}</TableCell>
                <TableCell align="right">
                  {hasStatistic ? resp.statistic.toFixed(4) : "—"}
                </TableCell>
                <TableCell align="right">
                  {formatPValue(resp.p_value)}
                </TableCell>
                <TableCell align="center">
                  <Chip
                    label={
                      resp.significant
                        ? t("models:label.notNormal")
                        : t("models:label.normal")
                    }
                    color={resp.significant ? "warning" : "success"}
                    size="small"
                    variant="outlined"
                  />
                </TableCell>
              </TableRow>
            );
          })}
        </TableBody>
      </Table>

      <TechnicalDetails
        sx={{ mt: 2 }}
        data={results.map(({ name, resp }) => ({
          run: name,
          statistic: resp.statistic,
          p_value: resp.p_value,
          significant: resp.significant,
          alpha: resp.alpha,
          details: resp.details,
        }))}
      />
    </Box>
  );
});

PerRunResults.propTypes = {
  results: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.number, PropTypes.string]),
      name: PropTypes.string,
      resp: PropTypes.object,
    }),
  ),
  title: PropTypes.string,
};

export default PerRunResults;
