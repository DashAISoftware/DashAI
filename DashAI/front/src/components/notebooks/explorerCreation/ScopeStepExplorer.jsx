import { useState } from "react";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import FormSchemaButtonGroup from "../../shared/FormSchemaButtonGroup";
import ColumnSelector from "../ColumnSelector";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";

export default function ScopeStepExplorer({
  notebook,
  tool,
  setScopeColumns,
  nextStep,
  hideButtons = false,
}) {
  const theme = useTheme();
  const [isSelectionValid, setIsSelectionValid] = useState(false);
  const allowedTypes = tool?.metadata?.allowed_types || [];
  const allowedDtypes = tool?.metadata?.allowed_dtypes || [];
  const inputCardinality = tool?.metadata?.input_cardinality || {};
  const nonAllowedDtypes = tool?.metadata?.non_allowed_dtypes || [];
  const tourContext = useTourContext();
  const { t } = useTranslation(["datasets", "common"]);

  const handleSubmit = () => {
    nextStep();
  };

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
      data-tour="column-selector-explorer-container"
    >
      {/* Content */}
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <Typography
          variant="body2"
          sx={{ color: theme.palette.text.primary, mb: 3 }}
        >
          {t("datasets:label.selectColumnsForExplorerScope")}
        </Typography>

        <ColumnSelector
          file_path={notebook.file_path}
          inputCardinality={inputCardinality}
          allowedTypes={allowedTypes}
          allowedDtypes={allowedDtypes}
          nonAllowedDtypes={nonAllowedDtypes}
          onSelectionChange={(selected) => setScopeColumns(selected)}
          onValidationChange={(isValid) => setIsSelectionValid(isValid)}
        />
      </Box>

      {/* Buttons */}
      {!hideButtons && (
        <FormSchemaButtonGroup
          onFormSubmit={handleSubmit}
          error={!isSelectionValid}
          saveButtonText={
            Object.values(tool.schema.properties).length > 0
              ? t("common:next")
              : t("common:save")
          }
          data-tour="explorer-scope-next-button"
        />
      )}
    </Box>
  );
}
