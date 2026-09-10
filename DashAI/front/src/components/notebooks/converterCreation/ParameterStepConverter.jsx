import React, { useEffect, useState } from "react";
import { Alert, Box, Typography } from "@mui/material";
import FormSchemaWithSelectedModel from "../../shared/FormSchemaWithSelectedModel";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";

export default function ParameterStepConverter({
  converter,
  tool,
  selectedColumns = [],
  initialParams,
  handleSaveConverter,
  setStep,
  hideButtons = false,
}) {
  const tourContext = useTourContext();
  const { t } = useTranslation(["common", "datasets"]);

  const handleSave = async (params) => {
    await handleSaveConverter(params);

    if (tourContext && tourContext.run) {
      setTimeout(() => {
        tourContext.nextStep();
      }, 500);
    }
  };

  useEffect(() => {
    if (tourContext?.run) {
      const timeout = setTimeout(() => {
        const button = document.querySelector(
          '[data-tour="create-converter-button"]',
        );
        if (button) {
          const dialogContent = button.closest(".MuiDialogContent-root");
          if (dialogContent) {
            const rect = button.getBoundingClientRect();
            const containerRect = dialogContent.getBoundingClientRect();
            const relativeTop = rect.top - containerRect.top;
            const scrollTop =
              dialogContent.scrollTop +
              relativeTop -
              dialogContent.clientHeight / 2 +
              rect.height / 2;

            dialogContent.scrollTo({
              top: Math.max(0, scrollTop),
              behavior: "smooth",
            });
          }
        }
      }, 500);

      return () => clearTimeout(timeout);
    }
  }, [tourContext?.stepIndex, tourContext?.run]);

  const nColumnsSelected = selectedColumns.length;
  const defaultNComponents =
    tool?.schema?.properties?.n_components?.default ?? null;
  const [currentNComponents, setCurrentNComponents] =
    useState(defaultNComponents);

  const isDimensionalityReduction =
    tool?.metadata?.n_components_features_bounded === true;

  const showNComponentsWarning =
    isDimensionalityReduction &&
    typeof currentNComponents === "number" &&
    nColumnsSelected > 0 &&
    currentNComponents > nColumnsSelected;

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
      data-tour="converter-parameters"
    >
      <Typography
        variant="h6"
        sx={{ fontWeight: 700, color: "primary.main", mb: 2 }}
      >
        {t("datasets:label.configureParameters")}
      </Typography>
      {showNComponentsWarning && (
        <Alert severity="warning" sx={{ mb: 2 }}>
          {t("datasets:label.nComponentsColumnInfo", {
            n: nColumnsSelected,
          })}
        </Alert>
      )}
      <FormSchemaContainer>
        <FormSchemaWithSelectedModel
          onFormSubmit={handleSave}
          modelToConfigure={converter}
          initialValues={initialParams}
          onCancel={() => setStep(0)}
          saveButtonText={t("datasets:button.createConverter")}
          hideButtons={hideButtons}
          onValuesChange={(values) => {
            if (values?.n_components !== undefined) {
              setCurrentNComponents(values.n_components);
            }
          }}
        />
      </FormSchemaContainer>
    </Box>
  );
}
