import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import OpenInFullIcon from "@mui/icons-material/OpenInFull";
import { useTranslation } from "react-i18next";
import HighlightedTextarea from "./HighlightedTextarea";
import PlaceholdersList from "./PlaceholdersList";
import { getDefaultPrompts } from "../../../api/rag";
import { LANGUAGE_CODES } from "../../../constants/languages";

/** The component a hand-written template is stored under. */
const CUSTOM_PROMPT_COMPONENT = "CustomRAGGenerationPrompt";

/**
 * Placeholders every RAG prompt has to contain, used until the registry's own
 * answer arrives (and if that request fails).
 */
const FALLBACK_REQUIRED = ["{chunks}", "{input}"];

/**
 * The prompt of one RAG session, edited in place.
 *
 * This replaced a picker over a shared prompt library. Prompt rows are
 * deduplicated by a hash of their parameters, so two sessions that chose the
 * same template shared one row: editing it rewrote the other session's prompt.
 * The template now lives in the session's own parameters, and the registry's
 * built-in templates are only ever used to seed it.
 *
 * Nothing is sent while typing. The panel's Save writes the whole draft, so a
 * half-finished template never reaches the pipeline.
 *
 * @param {object}   props
 * @param {object}   props.promptModel - The draft `{component, params}` ref.
 * @param {Function} props.setPromptModel - Replaces the draft ref.
 * @param {Function} [props.onValidityChange] - Called with whether the
 *   template has every required placeholder.
 * @returns {JSX.Element} The editor.
 */
export default function PromptEditor({
  promptModel,
  setPromptModel,
  onValidityChange,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const [seeds, setSeeds] = useState([]);
  const [placeholderSpec, setPlaceholderSpec] = useState({
    required: FALLBACK_REQUIRED,
    descriptions: {},
  });
  const [expanded, setExpanded] = useState(false);
  const textareaRef = useRef(null);
  const dialogTextareaRef = useRef(null);

  const template = promptModel?.params?.template ?? "";
  const language = promptModel?.params?.language ?? "en";

  useEffect(() => {
    let cancelled = false;
    getDefaultPrompts()
      .then((options) => {
        if (cancelled) return;
        // CustomRAGGenerationPrompt is the base class a hand-written template
        // is stored under, not a template to start from.
        setSeeds(options.filter((o) => o.name !== CUSTOM_PROMPT_COMPONENT));
        const base = options.find((o) => o.name === CUSTOM_PROMPT_COMPONENT);
        if (base?.metadata) {
          setPlaceholderSpec({
            required: base.metadata.required_placeholders ?? FALLBACK_REQUIRED,
            descriptions: base.metadata.placeholder_descriptions ?? {},
          });
        }
      })
      .catch((error) => {
        console.error("Failed to load prompt templates:", error);
        if (!cancelled) setSeeds([]);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const missing = useMemo(
    () => placeholderSpec.required.filter((ph) => !template.includes(ph)),
    [placeholderSpec, template],
  );

  useEffect(() => {
    onValidityChange?.(missing.length === 0);
  }, [missing, onValidityChange]);

  const update = useCallback(
    (params) => {
      setPromptModel({
        component: CUSTOM_PROMPT_COMPONENT,
        params: { template, language, ...params },
      });
    },
    [setPromptModel, template, language],
  );

  /**
   * Replaces the template with a registry template.
   *
   * Seeding is explicit rather than a side effect of picking a language: the
   * language select used to silently overwrite whatever the user had written.
   *
   * @param {string} name - The seed component's name.
   */
  const handleSeed = (name) => {
    const seed = seeds.find((option) => option.name === name);
    const seeded = seed?.metadata?.templates?.[language];
    if (seeded === undefined) return;
    update({ template: seeded });
  };

  const insertPlaceholder = useCallback(
    (placeholder) => {
      const textarea = expanded
        ? dialogTextareaRef.current
        : textareaRef.current;
      if (!textarea) {
        update({ template: template + placeholder });
        return;
      }
      const start = textarea.selectionStart;
      const end = textarea.selectionEnd;
      const next =
        template.substring(0, start) + placeholder + template.substring(end);
      update({ template: next });
      requestAnimationFrame(() => {
        const position = start + placeholder.length;
        textarea.selectionStart = position;
        textarea.selectionEnd = position;
        textarea.focus();
      });
    },
    [expanded, template, update],
  );

  const editor = (ref, minRows) => (
    <HighlightedTextarea
      ref={ref}
      value={template}
      onChange={(event) => update({ template: event.target.value })}
      minRows={minRows}
      placeholder={t("generative:rag.prompt.editor.templatePlaceholder")}
    />
  );

  return (
    <Stack spacing={2}>
      <Stack direction="row" spacing={1}>
        <TextField
          select
          size="small"
          fullWidth
          label={t("generative:rag.prompt.editor.startFrom")}
          value=""
          onChange={(event) => handleSeed(event.target.value)}
          helperText={t("generative:rag.prompt.editor.startFromHelp")}
        >
          {seeds.map((seed) => (
            <MenuItem key={seed.name} value={seed.name}>
              {seed.name}
            </MenuItem>
          ))}
        </TextField>
        <TextField
          select
          size="small"
          label={t("generative:rag.prompt.language")}
          value={language}
          onChange={(event) => update({ language: event.target.value })}
          sx={{ minWidth: 96 }}
        >
          {LANGUAGE_CODES.map((code) => (
            <MenuItem key={code} value={code}>
              {code}
            </MenuItem>
          ))}
        </TextField>
      </Stack>

      <PlaceholdersList
        required={placeholderSpec.required}
        descriptions={placeholderSpec.descriptions}
        template={template}
        onInsertPlaceholder={insertPlaceholder}
      />

      <Box>
        <Stack
          direction="row"
          alignItems="center"
          justifyContent="space-between"
        >
          <Typography variant="subtitle2">
            {t("generative:rag.prompt.editor.template")}
          </Typography>
          <Tooltip title={t("generative:rag.prompt.editor.expand")}>
            <IconButton
              size="small"
              onClick={() => setExpanded(true)}
              aria-label={t("generative:rag.prompt.editor.expand")}
            >
              <OpenInFullIcon fontSize="small" />
            </IconButton>
          </Tooltip>
        </Stack>
        {editor(textareaRef, 8)}
      </Box>

      {missing.length > 0 && (
        <Alert severity="error" sx={{ py: 0.5 }}>
          {t("generative:rag.prompt.editor.missingPlaceholder", {
            placeholders: missing.join(", "),
          })}
        </Alert>
      )}

      {/* The same controlled state, with room to read: eight rows in a panel
          this narrow is not enough for a real prompt. */}
      <Dialog
        open={expanded}
        onClose={() => setExpanded(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>{t("generative:rag.prompt.editor.template")}</DialogTitle>
        <DialogContent>
          <PlaceholdersList
            required={placeholderSpec.required}
            descriptions={placeholderSpec.descriptions}
            template={template}
            onInsertPlaceholder={insertPlaceholder}
          />
          {editor(dialogTextareaRef, 18)}
          {missing.length > 0 && (
            <Alert severity="error" sx={{ mt: 2, py: 0.5 }}>
              {t("generative:rag.prompt.editor.missingPlaceholder", {
                placeholders: missing.join(", "),
              })}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExpanded(false)}>
            {t("common:close")}
          </Button>
        </DialogActions>
      </Dialog>
    </Stack>
  );
}

PromptEditor.propTypes = {
  promptModel: PropTypes.shape({
    component: PropTypes.string,
    params: PropTypes.object,
  }),
  setPromptModel: PropTypes.func.isRequired,
  onValidityChange: PropTypes.func,
};
