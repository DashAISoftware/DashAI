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
import { formatPValue, formatStatistic } from "../../utils/statisticalTests";
import NotEvaluableCell from "./NotEvaluableCell";
import TechnicalDetails from "./TechnicalDetails";

/**
 * Renders the results of a per-run test, where the same test is applied
 * independently to each selected run (e.g. Shapiro-Wilk normality).
 *
 * Note on semantics: for normality tests, `significant === true` means the
 * null hypothesis of normality is rejected, i.e. the data is NOT normal.
 *
 * @param {object} props
 * @param {Array<{id:(number|string), name:string, resp:?object, error:?string}>} props.results
 *        One entry per run, each carrying its StatisticalTestResponse in
 *        `resp`, or `error` (and no `resp`) when the test could not be
 *        computed for that run.
 * @param {string} [props.title]  Heading (usually the test display name).
 */
const PerRunResults = forwardRef(function PerRunResults(
  { results, title },
  ref,
) {
  const { t } = useTranslation(["models", "common"]);

  if (!results || results.length === 0) return null;

  const evaluated = results.filter((r) => r.resp);
  const notEvaluatedCount = results.length - evaluated.length;
  const normalCount = evaluated.filter((r) => !r.resp.significant).length;
  const effectiveAlpha = evaluated[0]?.resp?.alpha;

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
        {evaluated.length > 0 && (
          <div>
            {t("models:label.normalityByRunSummary", {
              normal: normalCount,
              total: evaluated.length,
              alpha: effectiveAlpha,
            })}
          </div>
        )}
        {notEvaluatedCount > 0 && (
          <div>
            {t("models:label.runsNotEvaluated", {
              count: notEvaluatedCount,
              total: results.length,
            })}
          </div>
        )}
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
          {results.map(({ id, name, resp, error }) => (
            <TableRow key={id}>
              <TableCell>{name}</TableCell>
              {resp ? (
                <>
                  <TableCell align="right">
                    {formatStatistic(resp.statistic)}
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
                </>
              ) : (
                <NotEvaluableCell error={error} colSpan={3} />
              )}
            </TableRow>
          ))}
        </TableBody>
      </Table>

      <TechnicalDetails
        sx={{ mt: 2 }}
        data={results.map(({ name, resp, error }) =>
          resp
            ? {
                run: name,
                statistic: resp.statistic,
                p_value: resp.p_value,
                significant: resp.significant,
                alpha: resp.alpha,
                details: resp.details,
              }
            : { run: name, error },
        )}
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
      error: PropTypes.string,
    }),
  ),
  title: PropTypes.string,
};

export default PerRunResults;
