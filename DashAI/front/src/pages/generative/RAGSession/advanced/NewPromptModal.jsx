import React, { useState, useCallback, useEffect, useRef } from "react";
import CloseIcon from "@mui/icons-material/Close";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  Typography,
  Grid,
  IconButton,
  TextField,
  MenuItem,
  Box,
} from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import { generateSequentialName } from "../../../../utils/nameGenerator";
import PlaceholdersList from "../../../../components/generative/RAG/PlaceholdersList";
import HighlightedTextarea from "../../../../components/generative/RAG/HighlightedTextarea";
import { getCustomPrompts, createRAGPrompt } from "../../../../api/rag";
import { LANGUAGE_CODES } from "../../../../constants/languages";

/**
 * Modal dialog for creating a new custom RAG generation prompt.
 * Provides a form for the prompt name, language, template with placeholder insertion.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {function} props.handleClose - Callback to close the dialog.
 * @param {function} props.onPromptCreated - Callback invoked with the new prompt ID on success.
 * @param {Array} [props.existingPrompts=[]] - List of existing prompts for name generation.
 * @returns {JSX.Element} The new prompt modal.
 */
export default function NewPromptModal({
  open,
  handleClose,
  onPromptCreated,
  existingPrompts = [],
}) {
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["generative"]);
  const [promptTypes, setPromptTypes] = useState([]);
  const selectedPromptType = "CustomRAGGenerationPrompt";
  const [promptName, setPromptName] = useState("");
  const [promptTemplate, setPromptTemplate] = useState("");
  const [promptLanguage, setPromptLanguage] = useState("en");
  const [defaultPromptName, setDefaultPromptName] = useState("");
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false);
  const textareaRef = useRef(null);

  /**
   * Checks whether the prompt template contains all required placeholders.
   * @returns {boolean} True if every required placeholder is present in the template.
   */
  const allRequiredPresent = React.useMemo(() => {
    if (!selectedPromptType) return false;
    const selectedType = promptTypes.find(
      (type) => type.name === selectedPromptType,
    );
    if (!selectedType || !selectedType.metadata) return false;
    const required = selectedType.metadata.required_placeholders || [];
    return required.every((ph) => promptTemplate.includes(ph));
  }, [selectedPromptType, promptTypes, promptTemplate]);

  const canSave = Boolean(
    selectedPromptType && promptName.trim() && allRequiredPresent,
  );

  useEffect(() => {
    if (open) {
      getCustomPrompts()
        .then((data) => setPromptTypes(data))
        .catch(() => setPromptTypes([]));

      const generatedName = generateSequentialName({
        base: "Prompt",
        items: existingPrompts,
      });
      setDefaultPromptName(generatedName.defaultName);
      setPromptName(generatedName.defaultName);
      setPromptTemplate("");
      setPromptLanguage("en");
      setHasUnsavedChanges(false);
    }
  }, [open, existingPrompts]);

  /**
   * Updates the prompt name on user input.
   * @param {object} e - The input change event.
   */
  const handlePromptNameChange = useCallback((e) => {
    setPromptName(e.target.value);
    setHasUnsavedChanges(true);
  }, []);

  /**
   * Updates the prompt template text on user input.
   * @param {object} e - The textarea change event.
   */
  const handlePromptTemplateChange = useCallback((e) => {
    setPromptTemplate(e.target.value);
    setHasUnsavedChanges(true);
  }, []);

  /**
   * Inserts a placeholder string at the current cursor position in the
   * prompt template textarea. Replaces any selected text with the placeholder.
   * @param {string} placeholder - The placeholder string to insert (e.g. "{chunks}").
   */
  const handleInsertPlaceholder = useCallback(
    (placeholder) => {
      const textarea = textareaRef.current;
      if (!textarea) return;

      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const before = promptTemplate.substring(0, start);
      const after = promptTemplate.substring(end);

      setPromptTemplate(before + placeholder + after);
      setHasUnsavedChanges(true);

      // Restore cursor position right after the inserted placeholder
      requestAnimationFrame(() => {
        const pos = start + placeholder.length;
        textarea.selectionStart = pos;
        textarea.selectionEnd = pos;
        textarea.focus();
      });
    },
    [promptTemplate],
  );

  /**
   * Closes the modal after checking for unsaved changes; prompts for confirmation if needed.
   */
  const handleConfirmClose = useCallback(() => {
    if (hasUnsavedChanges) {
      const confirmed = window.confirm(
        t("generative:rag.newPrompt.unsavedChanges"),
      );
      if (!confirmed) return;
    }
    setHasUnsavedChanges(false);
    handleClose();
  }, [hasUnsavedChanges, handleClose, t]);

  /**
   * Creates the prompt via the API and calls onPromptCreated with the new ID on success.
   */
  const handleSave = useCallback(async () => {
    try {
      const result = await createRAGPrompt({
        class_name: selectedPromptType,
        name: promptName,
        parameters: {
          template: promptTemplate,
          ...(promptLanguage ? { language: promptLanguage } : {}),
        },
      });
      if (result && result.id) {
        enqueueSnackbar(t("generative:rag.newPrompt.success"), {
          variant: "success",
        });
        setHasUnsavedChanges(false);
        await onPromptCreated(result.id);
      }
    } catch (error) {
      console.error("Error creating prompt:", error);
      enqueueSnackbar(t("generative:rag.newPrompt.error"), {
        variant: "error",
      });
    }
  }, [
    promptName,
    promptTemplate,
    selectedPromptType,
    onPromptCreated,
    enqueueSnackbar,
    t,
  ]);

  const selectedType = promptTypes.find(
    (type) => type.name === selectedPromptType,
  );

  return (
    <Dialog
      open={open}
      onClose={handleConfirmClose}
      fullWidth
      maxWidth="md"
      aria-labelledby="new-prompt-dialog-title"
      PaperProps={{ sx: { minHeight: 600, borderRadius: 2 } }}
    >
      <DialogTitle id="new-prompt-dialog-title">
        <Grid container alignItems="center" justifyContent="space-between">
          <Grid item>
            <Typography variant="h6" component="h2">
              {t("generative:rag.newPrompt.title")}
            </Typography>
          </Grid>
          <Grid item>
            <IconButton edge="end" color="inherit" onClick={handleConfirmClose}>
              <CloseIcon />
            </IconButton>
          </Grid>
        </Grid>
      </DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 2 }}>
          <Typography variant="body2" color="textSecondary" sx={{ mb: 2 }}>
            {t("generative:rag.newPrompt.description")}
          </Typography>
          <Typography variant="body2" color="textSecondary">
            {t("generative:rag.newPrompt.placeholdersInfo")}
          </Typography>
        </Box>

        <TextField
          fullWidth
          label={t("generative:rag.newPrompt.nameLabel")}
          value={promptName}
          onChange={handlePromptNameChange}
          sx={{ mt: 2, mb: 2 }}
          required
          error={!promptName.trim()}
          helperText={
            !promptName.trim() ? t("generative:rag.newPrompt.nameRequired") : ""
          }
          InputLabelProps={{ required: false }}
        />

        <TextField
          select
          fullWidth
          label={t("generative:rag.newPrompt.languageLabel")}
          value={promptLanguage}
          onChange={(e) => {
            setPromptLanguage(e.target.value);
            setHasUnsavedChanges(true);
          }}
          sx={{ mb: 2 }}
        >
          <MenuItem value="">
            {t("generative:rag.promptView.languageNone")}
          </MenuItem>
          {LANGUAGE_CODES.map((code) => (
            <MenuItem key={code} value={code}>
              {t(`generative:rag.prompt.languages.${code}`)}
            </MenuItem>
          ))}
        </TextField>

        {selectedType && selectedType.metadata && (
          <PlaceholdersList
            required={selectedType.metadata.required_placeholders || []}
            descriptions={selectedType.metadata.placeholder_descriptions || {}}
            template={promptTemplate}
            onInsertPlaceholder={handleInsertPlaceholder}
          />
        )}

        <HighlightedTextarea
          ref={textareaRef}
          label={t("generative:rag.newPrompt.promptLabel")}
          placeholder={t("generative:rag.newPrompt.promptPlaceholder")}
          value={promptTemplate}
          onChange={handlePromptTemplateChange}
          minRows={6}
          sx={{ mt: 2 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={handleConfirmClose}>
          {t("generative:rag.newPrompt.cancel")}
        </Button>
        <Button variant="contained" disabled={!canSave} onClick={handleSave}>
          {t("generative:rag.newPrompt.save")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}
