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
import {
  getHypothesisDecisionMessage,
  formatPValue,
} from "../../utils/statisticalTests";
import TechnicalDetails from "./TechnicalDetails";

const POSTHOC_TEST_LABELS = {
  FriedmanTest: "models:label.nemenyiPairwiseComparisons",
  AnovaTest: "models:label.tukeyPairwiseComparisons",
};

/**
 * Renders the result of a single (omnibus) statistical test: statistic,
 * p-value, hypothesis decision, optional pairwise post-hoc table, and the
 * collapsible technical details.
 *
 * @param {object} props
 * @param {object} props.result  A StatisticalTestResponse object.
 * @param {string} [props.title]  Heading (usually the test display name).
 */
const SingleTestResult = forwardRef(function SingleTestResult(
  { result, title },
  ref,
) {
  const { t } = useTranslation(["models", "common"]);

  if (!result) return null;

  const hasPValue = result.p_value !== null && !isNaN(result.p_value);
  const hasStatistic = result.statistic !== null && !isNaN(result.statistic);

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
      <Box sx={{ display: "flex", alignItems: "center", gap: 1.5, mb: 2 }}>
        {title && <Typography variant="h6">{title}</Typography>}
        <Chip
          label={
            result.significant
              ? t("models:label.significant")
              : t("models:label.notSignificant")
          }
          color={result.significant ? "success" : "default"}
          size="small"
        />
      </Box>

      <Box
        sx={{
          display: "flex",
          gap: 3,
          mb: 2,
          p: 1.5,
          bgcolor: "action.hover",
          borderRadius: 1,
        }}
      >
        {hasStatistic && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              {t("models:label.statistic")}
            </Typography>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              {result.statistic?.toFixed(4)}
            </Typography>
          </Box>
        )}
        {hasPValue && (
          <Box>
            <Typography variant="caption" color="text.secondary">
              p-value
            </Typography>
            <Typography
              variant="body2"
              sx={{
                fontWeight: 600,
                color: result.significant ? "success.main" : "text.primary",
              }}
            >
              {formatPValue(result.p_value)}
            </Typography>
          </Box>
        )}
        <Box>
          <Typography variant="caption" color="text.secondary">
            α
          </Typography>
          <Typography variant="body2" sx={{ fontWeight: 600 }}>
            {result.alpha}
          </Typography>
        </Box>
      </Box>

      {hasPValue && (
        <Alert
          severity={result.significant ? "success" : "info"}
          sx={{ mb: 2, whiteSpace: "pre-line" }}
        >
          {getHypothesisDecisionMessage(
            result.significant,
            formatPValue(result.p_value),
            result.alpha,
            t,
          ) +
            "\n\n" +
            result.interpretation}
        </Alert>
      )}

      {result.posthoc && result.posthoc.length > 0 && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" sx={{ mb: 1, fontWeight: 600 }}>
            {t(POSTHOC_TEST_LABELS[result.test_name])}
          </Typography>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>{t("models:label.model1")}</TableCell>
                <TableCell>{t("models:label.model2")}</TableCell>
                <TableCell align="right">p-value</TableCell>
                <TableCell align="center">{t("models:label.result")}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {result.posthoc.map((pair, i) => (
                <TableRow key={i}>
                  <TableCell>{pair.run_1_name || pair.run_1}</TableCell>
                  <TableCell>{pair.run_2_name || pair.run_2}</TableCell>
                  <TableCell align="right">
                    {formatPValue(pair.p_value)}
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      label={
                        pair.significant
                          ? t("models:label.significant")
                          : t("models:label.notSignificant")
                      }
                      color={pair.significant ? "success" : "default"}
                      size="small"
                      variant="outlined"
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </Box>
      )}

      <TechnicalDetails data={result} />
    </Box>
  );
});

SingleTestResult.propTypes = {
  result: PropTypes.shape({
    test_name: PropTypes.string,
    statistic: PropTypes.number,
    p_value: PropTypes.number,
    significant: PropTypes.bool,
    alpha: PropTypes.number,
    interpretation: PropTypes.string,
    details: PropTypes.any,
    posthoc: PropTypes.array,
  }),
  title: PropTypes.string,
};

export default SingleTestResult;
