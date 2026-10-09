import ComponentSelector from "../../custom/ComponentSelector";
import { Box, CircularProgress, Stack } from "@mui/material";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";

/**
 * This component renders a selector for available dataloaders
 * @param {function} goToNextStep - Function to navigate to the next step in the dataset creation flow.
 * @param {function} goToPrevStep - Function to navigate back to the previous step in the dataset creation flow.
 * @param {object} selectedDataloader - The currently selected dataloader
 * @param {function} setSelectedDataloader - Function to update the selected dataloader
 * @param {Array} dataloaders - List of available dataloaders (fetched by parent)
 * @param {boolean} loadingDataloaders - Whether dataloaders are still loading
 */
export default function SelectDataloaderStep({
  goToNextStep,
  goToPrevStep,
  selectedDataloader,
  setSelectedDataloader,
  dataloaders = [],
  loadingDataloaders = false,
}) {
  const tourContext = useTourContext();
  const { t } = useTranslation(["datasets", "common"]);

  const handleNext = () => {
    goToNextStep();
    if (tourContext?.run) {
      const observer = new MutationObserver(() => {
        if (document.querySelector('[data-tour="upload-area"]')) {
          observer.disconnect();
          tourContext.nextStep();
        }
      });
      observer.observe(document.body, { childList: true, subtree: true });
    }
  };

  return (
    <Stack sx={{ height: "100%", minHeight: 0, flex: 1 }} spacing={4}>
      <Box sx={{ flex: 1, minHeight: 0 }}>
        {loadingDataloaders ? (
          <Box
            sx={{
              height: "100%",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <CircularProgress />
          </Box>
        ) : (
          <ComponentSelector
            components={dataloaders.map((d) => ({
              ...d,
              category: d.metadata?.category,
            }))}
            categoryKey="category"
            selected={selectedDataloader || null}
            onSelect={(item) => {
              setSelectedDataloader(item);
              const currentTarget =
                tourContext?.steps?.[tourContext?.stepIndex]?.target;
              if (
                tourContext?.run &&
                currentTarget === '[data-tour="csv-dataloader-option"]' &&
                item?.name?.toLowerCase().includes("csv")
              ) {
                tourContext.nextStep();
              }
            }}
            searchPlaceholder={t("datasets:searchDataloaders", {
              defaultValue: "Search data loaders...",
            })}
            tourDataFor={tourContext?.run ? "csv-dataloader-option" : null}
          />
        )}
      </Box>

      <StepperNavigationFooter
        onBack={goToPrevStep}
        onNext={handleNext}
        nextDisabled={!selectedDataloader?.name}
        nextDataTour={
          tourContext?.run ? "dataloader-step-next-button" : undefined
        }
      />
    </Stack>
  );
}
