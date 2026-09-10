import {
  Box,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useCallback, useEffect } from "react";
import { useTranslation } from "react-i18next";
import ComponentSelector from "../custom/ComponentSelector";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../credentials/credentialStatus";
import GenerativeBreadcrumbs from "./GenerativeBreadcrumbs";
import { useCreateSession } from "./CreateSessionContext";
import StepperNavigationFooter from "../shared/StepperNavigationFooter";
import { useTourContext } from "../tour/TourProvider";

export default function CreateSessionCenter() {
  const { t } = useTranslation(["generative", "common"]);
  const tourContext = useTourContext();

  useEffect(() => {
    if (!tourContext?.run) return;
    const currentTarget = tourContext.steps?.[tourContext.stepIndex]?.target;
    if (currentTarget === '[data-tour="task-gallery"]') {
      tourContext.resumeAtStep(tourContext.stepIndex);
    }
  }, []);

  const {
    step,
    models,
    loadingModels,
    markModelDownloaded,
    selectedModel,
    handleSelectModel,
    formik,
    submitting,
    handleNext,
    handleBack,
    handleCreate,
  } = useCreateSession();

  const handleSelectModelWithTour = useCallback(
    (model) => {
      handleSelectModel(model);
      if (tourContext?.run) tourContext.nextStep();
    },
    [handleSelectModel, tourContext],
  );

  const handleNextWithTour = useCallback(() => {
    if (tourContext?.run) tourContext.nextStep();
    handleNext();
  }, [handleNext, tourContext]);

  const handleCreateWithTour = useCallback(() => {
    if (tourContext?.run) tourContext.nextStep();
    handleCreate();
  }, [handleCreate, tourContext]);

  useEffect(() => {
    if (!tourContext?.run) return;
    const currentTarget = tourContext.steps?.[tourContext.stepIndex]?.target;
    if (
      currentTarget === '[data-tour="session-config"]' ||
      currentTarget === '[data-tour="model-parameters"]'
    ) {
      tourContext.resumeAtStep(tourContext.stepIndex);
    }
  }, [step]);

  // Read the download status from the (in place updated) models list so the
  // gate reacts to an inline download without needing selectedModel to change.
  const selectedModelState =
    models.find((m) => m.name === selectedModel?.name) || selectedModel;
  const selectedNeedsDownload =
    Boolean(selectedModelState?.metadata?.requires_download) &&
    !selectedModelState?.downloaded;

  // Credentials gate the same way downloads do: a model whose required
  // credentials are unmet cannot be used to create a session, even when it was
  // preselected via URL (which bypasses the disabled card in the selector).
  const { statuses, loaded } = useCredentialStatuses();
  const { locked: selectedCredentialsLocked } = getComponentCredentialState(
    selectedModelState || {},
    statuses,
    loaded,
  );
  const selectedUsable = !selectedNeedsDownload && !selectedCredentialsLocked;

  const canGoNext = !!selectedModel && selectedUsable;
  const canCreate =
    !!selectedModel &&
    selectedUsable &&
    !!formik.values.name?.trim() &&
    !submitting;

  return (
    <Box
      data-tour="task-gallery"
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        width: "100%",
        minHeight: 0,
        p: 4,
      }}
    >
      <GenerativeBreadcrumbs />
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h2">
          {step === 0
            ? t("generative:label.selectModel")
            : t("generative:label.configureSession")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {step === 0
            ? t("generative:label.pickAModelGroupedByTask")
            : t("generative:label.nameAndDescribeYourSession")}
        </Typography>
      </Box>

      <Box
        data-tour={step === 1 ? "session-config" : undefined}
        sx={{
          flex: 1,
          minHeight: 0,
          display: "flex",
          flexDirection: "column",
          overflowY: "auto",
          pt: 2,
          pb: 2,
        }}
      >
        {step === 0 ? (
          loadingModels ? (
            <Box
              sx={{
                flex: 1,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <CircularProgress />
            </Box>
          ) : (
            <ComponentSelector
              components={models}
              selected={selectedModel}
              onSelect={handleSelectModelWithTour}
              onDownloadChange={(model, isDownloaded) =>
                markModelDownloaded(model.name, isDownloaded)
              }
              categoryKey="task_display_name"
              searchPlaceholder={t("generative:label.searchModels")}
              tourDataFor={tourContext?.run ? "model-card-qwen" : null}
              tourDataMatchFn={(c) => c.name.toLowerCase().includes("qwen")}
            />
          )
        ) : (
          <Stack spacing={4} sx={{ maxWidth: "100%" }}>
            <TextField
              fullWidth
              label={t("generative:label.sessionName")}
              name="name"
              value={formik.values.name || ""}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
              error={Boolean(formik.touched.name && formik.errors.name)}
              helperText={formik.touched.name && formik.errors.name}
            />
            <TextField
              fullWidth
              multiline
              minRows={3}
              label={t("generative:label.sessionDescription")}
              name="description"
              value={formik.values.description || ""}
              onChange={formik.handleChange}
              onBlur={formik.handleBlur}
            />
          </Stack>
        )}
      </Box>

      <StepperNavigationFooter
        onBack={handleBack}
        onNext={step === 0 ? handleNextWithTour : handleCreateWithTour}
        backDisabled={submitting}
        nextDisabled={step === 0 ? !canGoNext : !canCreate}
        nextLabel={
          step === 0 ? t("common:next") : t("generative:button.createSession")
        }
        loading={submitting}
        variant={step === 0 ? "next" : "save"}
        nextDataTour={
          tourContext?.run
            ? step === 0
              ? "create-session-next"
              : "create-session-button"
            : null
        }
      />
    </Box>
  );
}
