import { useState } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTranslation } from "react-i18next";
import { FormSchemaProvider } from "../../../../contexts/schema";
import GeneratorConfigurationStep from "./GeneratorConfigurationStep";

/**
 * Full-screen modal dialog for advanced generator (LLM) configuration.
 * Wraps GeneratorConfigurationStep in a dialog with save/cancel actions.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {function} props.onClose - Callback to close the dialog.
 * @param {any} props.selectedGenerator - The currently selected generator paradigm.
 * @param {object} [props.generatorModel] - The current generator model { component, params }.
 * @param {function} props.setGeneratorModel - State setter for the generator model.
 * @returns {JSX.Element} The advanced generator modal.
 */
export default function GeneratorAdvancedModal({
  open,
  onClose,
  selectedGenerator,
  generatorModel,
  setGeneratorModel,
}) {
  const { t } = useTranslation(["generative"]);
  const [stepValid, setStepValid] = useState(false);

  /** Closes the modal without saving. */
  const handleClose = () => {
    onClose();
  };

  /** Saves and closes the modal. */
  const handleSave = () => {
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: { minHeight: "500px" },
      }}
    >
      <DialogTitle
        sx={{
          bgcolor: "background.paper",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {t("generative:rag.advanced.generatorTitle")}
        <IconButton
          onClick={handleClose}
          size="small"
          sx={{ color: "text.secondary" }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent
        dividers
        sx={{ bgcolor: "background.paper", minHeight: 400 }}
      >
        <FormSchemaProvider
          key={`generator-advanced-${generatorModel?.component}`}
        >
          <GeneratorConfigurationStep
            generatorModel={generatorModel}
            setGeneratorModel={setGeneratorModel}
            setNextEnabled={setStepValid}
          />
        </FormSchemaProvider>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button onClick={handleClose} variant="outlined">
          {t("generative:rag.advanced.close")}
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          color="primary"
          disabled={!stepValid}
        >
          {t("generative:rag.advanced.done")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
