import { useState, useRef } from "react";
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
import RetrieverConfigurationStep from "./RetrieverConfigurationStep";

/**
 * Full-screen modal dialog for advanced retriever configuration.
 * Wraps RetrieverConfigurationStep in a dialog with save/cancel actions.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {function} props.onClose - Callback to close the dialog.
 * @param {any} props.selectedParadigm - The currently selected retriever paradigm.
 * @param {Array} [props.allParadigms] - All available retriever paradigms.
 * @param {object} [props.retrieverModel] - The current retriever model.
 * @param {function} props.setRetrieverModel - State setter for the retriever model.
 * @returns {JSX.Element} The advanced retriever modal.
 */
export default function RetrieverAdvancedModal({
  open,
  onClose,
  selectedParadigm,
  allParadigms,
  retrieverModel,
  setRetrieverModel,
}) {
  const { t } = useTranslation(["generative"]);
  const [stepValid, setStepValid] = useState(false);
  const retrieverStepRef = useRef(null);

  /** Closes the modal without saving. */
  const handleClose = () => {
    onClose();
  };

  /**
   * Triggers a save of the current form values and closes the modal.
   */
  const handleSave = () => {
    if (retrieverStepRef.current) {
      retrieverStepRef.current.saveFormValues();
    }
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
        {t("generative:rag.advanced.retrieverTitle")}
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
          key={`retriever-advanced-${retrieverModel?.component}`}
        >
          <RetrieverConfigurationStep
            ref={retrieverStepRef}
            allParadigms={allParadigms}
            retrieverModel={retrieverModel}
            setRetrieverModel={setRetrieverModel}
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
