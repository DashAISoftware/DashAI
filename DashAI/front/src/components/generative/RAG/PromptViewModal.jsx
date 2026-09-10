import { useState, useMemo } from "react";
import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  MenuItem,
  Typography,
  Box,
  useTheme,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import { renderTemplateWithHighlights } from "../../../pages/generative/RAGSession/components/sectionUtils";
import { LANGUAGE_CODES } from "../../../constants/languages";

/**
 * Dialog that displays prompt content with optional language selection.
 *
 * Supports two prompt shapes:
 *  - Single-template: content in `prompt.parameters.template` (string)
 *  - Multi-template: content in `prompt.parameters.templates` (dict of `{ [lang]: string }`)
 *
 * For multi-template prompts, a language selector is enabled so the user can
 * switch between available language versions. For single-template prompts,
 * the selector is disabled and shows either the stored language or
 * "Language not available".
 *
 * The parent must pass a unique `key` prop (e.g. `prompt.id`) to ensure state
 * resets when a different prompt is displayed (component is always mounted).
 *
 * @param {object}  props
 * @param {boolean} props.open                         - Whether the dialog is visible
 * @param {function} props.handleClose                  - Callback when the dialog is closed
 * @param {object}  [props.prompt]                      - The prompt object to display
 * @param {string}  props.prompt.name                   - Display name (shown in title bar)
 * @param {string}  props.prompt.class_name             - Component type (shown as "Type")
 * @param {object}  props.prompt.parameters             - Parameters bag
 * @param {string}  [props.prompt.parameters.template]  - Single template string
 * @param {object}  [props.prompt.parameters.templates] - Multi-language template dict
 * @param {string}  [props.prompt.parameters.language]  - Default language code
 */
export default function PromptViewModal({ open, handleClose, prompt }) {
  const { t } = useTranslation(["generative"]);
  const theme = useTheme();

  const placeholderColors = useMemo(
    () => ({
      bg: theme.palette.placeholder?.bg || theme.palette.warning.light,
      text: theme.palette.placeholder?.text || theme.palette.warning.dark,
    }),
    [theme],
  );

  const hasMultiTemplates = useMemo(
    () =>
      !!prompt?.parameters?.templates &&
      Object.keys(prompt.parameters.templates).length > 0,
    [prompt],
  );

  const [selectedLanguage, setSelectedLanguage] = useState(() => {
    if (prompt?.parameters?.templates) {
      return (
        prompt?.parameters?.language ||
        Object.keys(prompt.parameters.templates)[0] ||
        ""
      );
    }
    return "";
  });

  /** Language options derived from available template keys for multi-template prompts. */
  const languageOptions = useMemo(() => {
    if (!hasMultiTemplates || !prompt?.parameters?.templates) return [];
    const codes = Object.keys(prompt.parameters.templates);
    return codes.map((code) => ({
      code,
      name: t(`generative:rag.prompt.languages.${code}`) || code,
    }));
  }, [hasMultiTemplates, prompt, t]);

  const currentTemplate = useMemo(() => {
    if (hasMultiTemplates) {
      return prompt?.parameters?.templates?.[selectedLanguage] || "";
    }
    return prompt?.parameters?.template || "";
  }, [hasMultiTemplates, prompt, selectedLanguage]);

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {prompt?.name || t("generative:rag.promptView.untitledPrompt")}
      </DialogTitle>
      <DialogContent>
        <TextField
          label={t("generative:rag.promptView.type")}
          value={prompt?.class_name || ""}
          disabled
          fullWidth
          size="small"
          sx={{ mt: 1, mb: 2 }}
        />

        {hasMultiTemplates ? (
          <TextField
            select
            label={t("generative:rag.promptView.language")}
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            fullWidth
            size="small"
            sx={{ mb: 2 }}
          >
            {languageOptions.map((opt) => (
              <MenuItem key={opt.code} value={opt.code}>
                {opt.name}
              </MenuItem>
            ))}
          </TextField>
        ) : (
          <TextField
            label={t("generative:rag.promptView.language")}
            value={
              prompt?.parameters?.language
                ? t(
                    `generative:rag.prompt.languages.${prompt.parameters.language}`,
                  ) || prompt.parameters.language
                : t("generative:rag.promptView.languageNotAvailable")
            }
            disabled
            fullWidth
            size="small"
            sx={{ mb: 2 }}
          />
        )}

        <Typography variant="subtitle2" gutterBottom>
          {t("generative:rag.promptView.templateContent")}
        </Typography>
        <Box
          sx={{
            p: 2,
            backgroundColor: theme.palette.ui.box,
            border: "1px solid",
            borderColor: theme.palette.ui.border,
            borderRadius: 1,
            fontFamily: theme.typography.code.fontFamily,
            lineHeight: 1.6,
            whiteSpace: "pre-wrap",
            wordBreak: "break-word",
            maxHeight: "400px",
            overflowY: "auto",
          }}
        >
          {renderTemplateWithHighlights(
            currentTemplate,
            placeholderColors,
            theme.typography.code.fontFamily,
          ) ?? (
            <Typography
              variant="body2"
              color="text.secondary"
              fontStyle="italic"
            >
              {hasMultiTemplates
                ? t("generative:rag.promptView.languageNotAvailable")
                : t("generative:rag.promptView.noContent")}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>
          {t("generative:rag.promptView.close")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

PromptViewModal.propTypes = {
  open: PropTypes.bool.isRequired,
  handleClose: PropTypes.func.isRequired,
  prompt: PropTypes.shape({
    id: PropTypes.number,
    name: PropTypes.string,
    class_name: PropTypes.string,
    parameters: PropTypes.shape({
      template: PropTypes.string,
      templates: PropTypes.objectOf(PropTypes.string),
      language: PropTypes.string,
    }),
  }),
};
