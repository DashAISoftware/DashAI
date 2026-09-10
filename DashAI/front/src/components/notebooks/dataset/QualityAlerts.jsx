import React, { useCallback, useMemo } from "react";
import {
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Typography,
  Box,
} from "@mui/material";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import CheckCircleOutlineIcon from "@mui/icons-material/CheckCircleOutline";
import WarningAmberIcon from "@mui/icons-material/WarningAmber";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";

export const QualityAlerts = ({
  qualityInfo,
  generalInfo,
  missingValues,
  onNavigateTab,
}) => {
  const theme = useTheme();
  const { t } = useTranslation(["datasets"]);
  const context = useDatasetsAndNotebooks();
  const setDatasetTab = onNavigateTab ?? context?.setDatasetTab ?? (() => {});

  const handleNavigate = useCallback(
    (section) => {
      setDatasetTab(0);
      setTimeout(() => {
        const el = document.querySelector(`[data-section="${section}"]`);
        if (el) {
          el.scrollIntoView({ behavior: "smooth", block: "center" });
          el.style.transition = "box-shadow 0.3s";
          el.style.boxShadow = `0 0 0 2px ${theme.palette.warning.main}`;
          setTimeout(() => {
            el.style.boxShadow = "";
          }, 2000);
        }
      }, 100);
    },
    [setDatasetTab, theme],
  );

  const { warnings, successes } = useMemo(() => {
    const w = [];
    const s = [];

    if (!qualityInfo) {
      return { warnings: w, successes: s };
    }

    // Duplicate rows
    if (generalInfo?.duplicate_rows > 0) {
      w.push({
        key: "duplicates",
        severity: "warning",
        message: t("datasets:label.foundDuplicateRows", {
          count: generalInfo.duplicate_rows,
        }),
      });
    } else {
      s.push({
        key: "no-duplicates",
        message: t("datasets:label.noDuplicateRows"),
      });
    }

    // Missing values
    if (
      missingValues &&
      Object.values(missingValues).some((value) => value > 0)
    ) {
      w.push({
        key: "nan",
        severity: "warning",
        navigateTo: "missing-values-overview",
        message: t("datasets:label.missingValuesDetected", {
          columns: Object.entries(missingValues)
            .filter(([_, value]) => value > 0)
            .map(([key, _]) => key)
            .join(", "),
        }),
      });
    } else {
      s.push({
        key: "no-missing",
        message: t("datasets:label.noMissingValues"),
      });
    }

    // High cardinality columns
    if (qualityInfo.high_cardinality_columns?.length > 0) {
      w.push({
        key: "cardinality",
        severity: "info",
        message: t("datasets:label.highCardinalityDetected", {
          columns: qualityInfo.high_cardinality_columns.join(", "),
        }),
      });
    }

    return { warnings: w, successes: s };
  }, [qualityInfo, generalInfo, missingValues, t]);

  if (!qualityInfo) return null;

  const hasIssues = warnings.length > 0;

  return (
    <Accordion
      defaultExpanded={false}
      disableGutters
      sx={{
        boxShadow: "none",
        border: (theme) =>
          `1px solid ${hasIssues ? theme.palette.warning.main : theme.palette.success.main}`,
        borderRadius: "8px !important",
        bgcolor: (theme) =>
          hasIssues
            ? `${theme.palette.warning.main}40`
            : `${theme.palette.success.main}40`,
        "&::before": { display: "none" },
        "&.Mui-expanded": { margin: 0 },
      }}
    >
      <AccordionSummary
        expandIcon={<ExpandMoreIcon />}
        sx={{
          minHeight: 48,
          "&.Mui-expanded": { minHeight: 48 },
          "& .MuiAccordionSummary-content": { my: 2 },
        }}
      >
        <Box sx={{ display: "flex", alignItems: "center", gap: 2 }}>
          {hasIssues ? (
            <WarningAmberIcon color="warning" sx={{ fontSize: 24 }} />
          ) : (
            <CheckCircleOutlineIcon color="success" sx={{ fontSize: 24 }} />
          )}
          <Typography variant="subtitle2" fontWeight="bold">
            {t("datasets:label.dataQualitySummary")}
          </Typography>
          <Typography
            variant="caption"
            sx={{
              color: (theme) =>
                hasIssues
                  ? theme.palette.warning.main
                  : theme.palette.success.main,
              fontWeight: "bold",
            }}
          >
            —{" "}
            {hasIssues
              ? t("datasets:label.qualityIssuesFound", {
                  count: warnings.length,
                })
              : t("datasets:label.noDataQualityIssuesDetected")}
          </Typography>
        </Box>
      </AccordionSummary>
      <AccordionDetails sx={{ pt: 0, pb: 3 }}>
        {warnings.map((item) => (
          <Alert
            severity={item.severity}
            sx={{
              mb: 2,
              ...(item.navigateTo && {
                cursor: "pointer",
                transition: "opacity 0.2s",
                "&:hover": { opacity: 0.8 },
              }),
            }}
            key={item.key}
            onClick={
              item.navigateTo
                ? () => handleNavigate(item.navigateTo)
                : undefined
            }
          >
            {item.message}
          </Alert>
        ))}
        {successes.map((item) => (
          <Alert severity="success" sx={{ mb: 2 }} key={item.key}>
            {item.message}
          </Alert>
        ))}
      </AccordionDetails>
    </Accordion>
  );
};
