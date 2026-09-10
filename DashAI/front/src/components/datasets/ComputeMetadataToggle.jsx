import { Alert, Box, FormControlLabel, Stack, Switch } from "@mui/material";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { shouldRecommendDisableMetadata } from "../../utils/metadataRecommendation";

function formatRows(n) {
  if (!n) return "?";
  if (n >= 1_000_000) return `~${(n / 1_000_000).toFixed(1)}M`;
  if (n >= 1_000) return `~${Math.round(n / 1_000)}k`;
  return `${n}`;
}

export default function ComputeMetadataToggle({
  value,
  onChange,
  colCount,
  estRows,
  disabled = false,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const recommendDisable = shouldRecommendDisableMetadata({
    colCount,
    estRows,
  });

  return (
    <Stack spacing={1} sx={{ width: "100%" }}>
      <FormControlLabel
        control={
          <Switch
            checked={value}
            onChange={(e) => onChange(e.target.checked)}
            disabled={disabled}
            data-testid="compute-metadata-toggle"
          />
        }
        label={t("datasets:computeMetadata.label")}
      />
      <Box sx={{ ml: 4, color: "text.secondary", fontSize: 13 }}>
        {t("datasets:computeMetadata.helper")}
      </Box>
      {recommendDisable && (
        <Alert
          severity="info"
          sx={{ ml: 4 }}
          data-testid="compute-metadata-alert"
        >
          {t("datasets:computeMetadata.recommendation", {
            colCount,
            estRows: formatRows(estRows),
          })}
        </Alert>
      )}
    </Stack>
  );
}

ComputeMetadataToggle.propTypes = {
  value: PropTypes.bool.isRequired,
  onChange: PropTypes.func.isRequired,
  colCount: PropTypes.number,
  estRows: PropTypes.number,
  disabled: PropTypes.bool,
};
