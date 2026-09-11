import React, { useMemo } from "react";
import PropTypes from "prop-types";
import { Box, Stack, Tooltip, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import SplitsCard from "./SplitsCard";
import { buildSplitPreview, SPLIT_ROLES } from "../../../utils/splitPreview";

const LEGEND_ORDER = [
  SPLIT_ROLES.TRAIN,
  SPLIT_ROLES.VALIDATION,
  SPLIT_ROLES.TEST,
  SPLIT_ROLES.UNUSED,
];

const roleColors = (theme) => {
  const [green, , orange] = theme.palette.chart?.palette ?? [];
  return {
    [SPLIT_ROLES.TRAIN]: theme.palette.primary.main,
    [SPLIT_ROLES.VALIDATION]: orange ?? theme.palette.warning.main,
    [SPLIT_ROLES.TEST]: green ?? theme.palette.success.main,
    [SPLIT_ROLES.UNUSED]: theme.palette.action.disabledBackground,
  };
};

const asPercent = (fraction) => Math.round((fraction ?? 0) * 100);

function SplitPreview({
  geometry,
  description,
  splitterDescription,
  splitType,
  params,
  indexes,
  datasetInfo,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["experiments", "common"]);

  const preview = useMemo(
    () =>
      buildSplitPreview({
        geometry,
        splitType,
        params,
        indexes,
        datasetInfo,
      }),
    [geometry, splitType, params, indexes, datasetInfo],
  );

  const explainers = [description, splitterDescription].filter(Boolean);

  const colors = roleColors(theme);

  const roleLabel = (role) =>
    role === SPLIT_ROLES.UNUSED
      ? t("experiments:splitPreview.unused")
      : t(`common:${role}`);

  if (!preview) {
    return (
      <SplitsCard label={t("experiments:splitPreview.title")}>
        <Stack spacing={2}>
          {explainers.map((explainer) => (
            <Typography
              key={explainer}
              variant="caption"
              color="text.secondary"
            >
              {explainer}
            </Typography>
          ))}
          <Typography variant="caption" color="text.secondary">
            {t("experiments:splitPreview.unavailable")}
          </Typography>
        </Stack>
      </SplitsCard>
    );
  }

  const { rows, notes, error, shares } = preview;
  const legendRoles = LEGEND_ORDER.filter(
    (role) => (shares[role] ?? 0) > 0.0001,
  );

  return (
    <SplitsCard label={t("experiments:splitPreview.title")}>
      <Stack spacing={3}>
        {explainers.length > 0 && (
          <Stack spacing={2}>
            {explainers.map((explainer) => (
              <Typography
                key={explainer}
                variant="caption"
                color="text.secondary"
              >
                {explainer}
              </Typography>
            ))}
          </Stack>
        )}

        {error ? (
          <Typography variant="caption" color="error.main">
            {t(`experiments:splitPreview.error.${error.key}`, error.values)}
          </Typography>
        ) : (
          <Stack spacing={1}>
            {rows.map((row) =>
              row.ellipsis ? (
                <Box
                  key={row.key}
                  sx={{ display: "flex", alignItems: "center", gap: 2 }}
                >
                  <Box sx={{ width: 58, flexShrink: 0 }} />
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    sx={{ lineHeight: 1 }}
                  >
                    {t("experiments:splitPreview.moreFolds", {
                      hidden: row.hiddenCount,
                    })}
                  </Typography>
                </Box>
              ) : (
                <Box
                  key={row.key}
                  sx={{ display: "flex", alignItems: "center", gap: 2 }}
                >
                  <Typography
                    variant="caption"
                    color="text.secondary"
                    noWrap
                    sx={{ width: 58, flexShrink: 0, fontSize: "0.68rem" }}
                  >
                    {t(row.labelKey, row.labelValues)}
                  </Typography>
                  <Box
                    sx={{
                      display: "flex",
                      flex: 1,
                      height: 14,
                      borderRadius: 0.5,
                      overflow: "hidden",
                      backgroundColor: colors[SPLIT_ROLES.UNUSED],
                    }}
                  >
                    {row.segments.map((piece, index) => (
                      <Tooltip
                        key={`${row.key}-${index}`}
                        title={`${roleLabel(piece.role)} ${asPercent(
                          piece.fraction,
                        )}%`}
                        arrow
                      >
                        <Box
                          sx={{
                            width: `${piece.fraction * 100}%`,
                            minWidth: 2,
                            backgroundColor: colors[piece.role],
                            borderRight:
                              index < row.segments.length - 1
                                ? `1px solid ${theme.palette.background.paper}`
                                : "none",
                          }}
                        />
                      </Tooltip>
                    ))}
                  </Box>
                </Box>
              ),
            )}
          </Stack>
        )}

        {!error && legendRoles.length > 0 && (
          <Stack direction="row" flexWrap="wrap" sx={{ gap: 3 }}>
            {legendRoles.map((role) => (
              <Box
                key={role}
                sx={{ display: "flex", alignItems: "center", gap: 1 }}
              >
                <Box
                  sx={{
                    width: 8,
                    height: 8,
                    borderRadius: "2px",
                    backgroundColor: colors[role],
                  }}
                />
                <Typography
                  variant="caption"
                  color="text.secondary"
                  sx={{ fontSize: "0.68rem" }}
                >
                  {`${roleLabel(role)} ${asPercent(shares[role])}%`}
                </Typography>
              </Box>
            ))}
          </Stack>
        )}

        {notes.length > 0 && (
          <Stack spacing={0.5}>
            {notes.map((note) => (
              <Typography
                key={note.key}
                variant="caption"
                color="text.secondary"
                sx={{ fontSize: "0.68rem", lineHeight: 1.4 }}
              >
                {t(`experiments:splitPreview.notes.${note.key}`, note.values)}
              </Typography>
            ))}
          </Stack>
        )}
      </Stack>
    </SplitsCard>
  );
}

SplitPreview.propTypes = {
  geometry: PropTypes.string,
  description: PropTypes.string,
  splitterDescription: PropTypes.string,
  splitType: PropTypes.string,
  params: PropTypes.object,
  indexes: PropTypes.object,
  datasetInfo: PropTypes.object,
};

export default SplitPreview;
