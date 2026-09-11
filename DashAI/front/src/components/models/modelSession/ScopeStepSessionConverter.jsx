import { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import ColumnSelector from "../../notebooks/ColumnSelector";
import FormSchemaButtonGroup from "../../shared/FormSchemaButtonGroup";
import { buildColumnKeysAndTypes, keyToRef } from "./sessionColumnRefs";

/**
 * Scope step for a converter being added to a session's preprocessing
 * sequence: column selection only (there's no row-level scope — the
 * train/test split doesn't exist yet at config time, and a session
 * converter never sees rows outside its own fold's training partition at
 * fit time regardless of what's picked here).
 *
 * The scope offered isn't just the dataset's raw columns: it's every raw
 * column plus one synthetic key per output group of every converter
 * already configured *before* this one in the sequence (chaining). The
 * shared `ColumnSelector` only knows a plain `{name: {type, dtype}}` map,
 * so groups are represented as synthetic keys built by `sessionColumnRefs`
 * and translated back into real ColumnRef scope entries once the user
 * picks a selection.
 */
export default function ScopeStepSessionConverter({
  tool,
  datasetTypes,
  preprocessing,
  filePath,
  scope,
  setScope,
  nextStep,
  convertersMeta,
}) {
  const theme = useTheme();
  const { t } = useTranslation(["common", "datasets", "models"]);
  const [isColumnSelectionValid, setIsColumnSelectionValid] = useState(false);

  const allowedTypes = tool?.metadata?.allowed_types || [];
  const allowedDtypes = tool?.metadata?.allowed_dtypes || [];
  const nonAllowedDtypes = tool?.metadata?.non_allowed_dtypes || [];
  const inputCardinality = tool?.metadata?.input_cardinality || {};

  const { columnTypes: columnTypesForSelector, optionLabels } = useMemo(
    () =>
      buildColumnKeysAndTypes({ datasetTypes, preprocessing, convertersMeta }),
    [datasetTypes, preprocessing, convertersMeta],
  );

  const handleSelectionChange = (selected) => {
    setScope(selected.map((col) => keyToRef(col.columnName)));
  };

  const hasParams = Object.values(tool.schema.properties).length > 0;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        flex: 1,
        height: "100%",
        gap: 2,
        minHeight: 0,
      }}
    >
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.primary, mb: 1 }}
        >
          {t("datasets:label.selectScopeDescriptionColumns")}
        </Typography>
        <ColumnSelector
          file_path={filePath}
          tool={tool}
          allowedTypes={allowedTypes}
          allowedDtypes={allowedDtypes}
          nonAllowedDtypes={nonAllowedDtypes}
          inputCardinality={inputCardinality}
          columnTypes={columnTypesForSelector}
          optionLabels={optionLabels}
          onSelectionChange={handleSelectionChange}
          onValidationChange={setIsColumnSelectionValid}
        />
      </Box>
      <Box sx={{ display: "flex", alignItems: "center", gap: 1 }}>
        <Box sx={{ flexGrow: 1 }}>
          <FormSchemaButtonGroup
            onFormSubmit={nextStep}
            error={!isColumnSelectionValid}
            saveButtonText={
              hasParams ? t("common:next") : t("models:button.addConverter")
            }
            sx={{ borderTop: 0, pt: 0, mt: 0 }}
          />
        </Box>
      </Box>
    </Box>
  );
}

ScopeStepSessionConverter.propTypes = {
  tool: PropTypes.object.isRequired,
  datasetTypes: PropTypes.object.isRequired,
  preprocessing: PropTypes.array,
  filePath: PropTypes.string,
  scope: PropTypes.array.isRequired,
  setScope: PropTypes.func.isRequired,
  nextStep: PropTypes.func.isRequired,
  convertersMeta: PropTypes.object,
};
