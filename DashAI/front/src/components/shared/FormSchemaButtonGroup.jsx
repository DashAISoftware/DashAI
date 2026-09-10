import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import StepperNavigationFooter from "./StepperNavigationFooter";

function FormSchemaButtonGroup({
  onCancel,
  onFormSubmit,
  autoSave,
  formik,
  error,
  saveButtonText,
  backButtonText,
  dataTour,
  sx,
}) {
  const { t } = useTranslation(["common", "datasets"]);
  const finalSaveText = saveButtonText ?? t("common:save");
  const finalBackText = backButtonText ?? t("common:back");

  const isCreateExplorer =
    saveButtonText === t("datasets:button.createExplorer");
  const isCreateConverter =
    saveButtonText === t("datasets:button.createConverter");
  const finalDataTour =
    dataTour ||
    (isCreateExplorer
      ? "create-explorer-button"
      : isCreateConverter
        ? "create-converter-button"
        : undefined);

  const isFormValid =
    !autoSave && Object.keys(formik?.errors ?? {}).length === 0 && !error;

  if (autoSave) {
    return null;
  }

  return (
    <StepperNavigationFooter
      onBack={onCancel}
      onNext={onFormSubmit}
      nextDisabled={!isFormValid}
      backLabel={finalBackText}
      nextLabel={finalSaveText}
      showBack={!!onCancel}
      showNext={!!onFormSubmit}
      nextDataTour={finalDataTour}
      sx={sx}
    />
  );
}

FormSchemaButtonGroup.propTypes = {
  onCancel: PropTypes.func,
  onFormSubmit: PropTypes.func,
  autoSave: PropTypes.bool,
  formik: PropTypes.object,
  error: PropTypes.bool,
  saveButtonText: PropTypes.string,
  backButtonText: PropTypes.string,
  dataTour: PropTypes.string,
  sx: PropTypes.object,
};

export default FormSchemaButtonGroup;
