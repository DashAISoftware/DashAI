import { useState, useEffect, useCallback, useMemo, useRef } from "react";
import {
  Box,
  Typography,
  Card,
  CardContent,
  Autocomplete,
  TextField,
  Button,
  MenuItem,
  useTheme,
} from "@mui/material";
import { useNavigate } from "react-router-dom";
import {
  ViewList as ViewListIcon,
  Info as InfoIcon,
  ExpandMore as ExpandMoreIcon,
  AddCircleOutline as AddIcon,
} from "@mui/icons-material";
import IconButton from "@mui/material/IconButton";
import Tooltip from "@mui/material/Tooltip";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  getRAGPrompts,
  getDefaultPrompts,
  isGenerationPromptClass,
} from "../../../api/rag";
import NewPromptModal from "../../../pages/generative/RAGSession/advanced/NewPromptModal";
import RAGSectionColumn from "../../../pages/generative/RAGSession/components/RAGSectionColumn";
import {
  getDescription,
  renderTemplateWithHighlights,
} from "../../../pages/generative/RAGSession/components/sectionUtils";

import { LANGUAGE_CODES } from "../../../constants/languages";

const CREATE_NEW_ID = "__create-new__";
const DEFAULT_IDS = {
  DefaultRAGGenerationPrompt: "default-generation",
  DefaultQARAGGenerationPrompt: "default-QA",
};

/**
 * Returns the translated display name for a default prompt option.
 * @param {object} option - The prompt option object.
 * @param {function} t - i18n translate function.
 * @returns {string}
 */
function getDefaultDisplayName(option, t) {
  // Use class_name (set explicitly by our code) rather than name
  // (raw API field) to avoid potential encoding / serialization mismatches.
  const cname = option.class_name || option.name || "";
  if (cname.includes("DefaultQARAGGenerationPrompt")) {
    return t("generative:rag.prompt.defaultQAGenerationPrompt");
  }
  if (cname.includes("DefaultRAGGenerationPrompt")) {
    return t("generative:rag.prompt.defaultGenerationPrompt");
  }
  return option.name || cname;
}

/**
 * Returns the display label for a given prompt option (default, custom, or "create new").
 * @param {object} option - The prompt option object.
 * @param {function} t - i18n translate function.
 * @returns {string}
 */
function getOptionLabel(option, t) {
  if (option._isCreateNew) return option.name;
  if (option._isDefault) return getDefaultDisplayName(option, t);
  return option.name;
}

/**
 * Card for selecting and viewing a prompt template (default or custom), with
 * language switcher, description toggle, and inline template preview with highlights.
 *
 * @param {object}   props
 * @param {object}   props.promptModel - { component: string, params: { template, language, ... } }
 * @param {function} props.setPromptModel - State setter for promptModel.
 * @param {function} [props.onTokenCountChange] - Callback with estimated token count of the selected template.
 * @returns {JSX.Element|null}
 */
export default function PromptParamsCard({
  promptModel,
  setPromptModel,
  onTokenCountChange,
}) {
  const navigate = useNavigate();
  const goToPromptsDetail = () => navigate("/app/generative/rag/prompts");
  const { t, i18n } = useTranslation(["generative"]);
  const theme = useTheme();
  const placeholderColors = useMemo(
    () => ({
      bg: theme.palette.placeholder?.bg || theme.palette.warning.light,
      text: theme.palette.placeholder?.text || theme.palette.warning.dark,
    }),
    [theme],
  );
  const [showDescription, setShowDescription] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);

  const platformLang = useMemo(() => {
    const lang = (i18n.language || "en").split("-")[0];
    return ["en", "es", "pt"].includes(lang) ? lang : "en";
  }, [i18n.language]);

  const [customPrompts, setCustomPrompts] = useState([]);
  const [defaultPrompts, setDefaultPrompts] = useState([]);
  const [selectedPrompt, setSelectedPrompt] = useState(null);
  const [newPromptModalOpen, setNewPromptModalOpen] = useState(false);
  const [loading, setLoading] = useState(true);
  const [selectedLanguage, setSelectedLanguage] = useState(platformLang);
  const prevSelectedRef = useRef(null);
  const isInitializedRef = useRef(false);

  /**
   * Loads custom RAG prompts and default prompt templates from the API.
   * Excludes system defaults from custom prompts and CustomRAGGenerationPrompt from defaults.
   */
  const loadPrompts = useCallback(async () => {
    try {
      const dbPrompts = await getRAGPrompts();
      // Keep only user-created generation prompts:
      // 1. Exclude system defaults (class_name starts with "Default")
      // 2. Exclude augmentation prompts (wrong type for this selector)
      setCustomPrompts(
        (dbPrompts || []).filter(
          (p) =>
            !p.class_name.startsWith("Default") &&
            isGenerationPromptClass(p.class_name),
        ),
      );
    } catch (error) {
      console.error("Error loading custom RAG prompts:", error);
      setCustomPrompts([]);
    }

    try {
      const defaultData = await getDefaultPrompts();
      // Filter out CustomRAGGenerationPrompt — it's a base class for
      // user-created prompts, not a selectable template. It has no
      // templates in its metadata and inherits a generic description
      // ("Base class for RAG prompts.") from Prompt.
      setDefaultPrompts(
        (defaultData || []).filter(
          (dp) => dp.name !== "CustomRAGGenerationPrompt",
        ),
      );
    } catch (error) {
      console.error("Error loading default RAG prompts:", error);
      setDefaultPrompts([]);
    }
  }, []);

  useEffect(() => {
    const load = async () => {
      await loadPrompts();
      setLoading(false);
    };
    load();
  }, [loadPrompts]);

  const mergedOptions = useMemo(() => {
    const defaults = defaultPrompts.map((dp) => ({
      ...dp,
      id: DEFAULT_IDS[dp.name] || dp.name,
      _isDefault: true,
      class_name: dp.name,
    }));
    const customs = customPrompts.map((cp) => ({
      ...cp,
      _isDefault: false,
    }));
    return [
      ...defaults,
      ...customs,
      {
        id: CREATE_NEW_ID,
        name: t("generative:rag.prompt.createNewPrompt"),
        _isCreateNew: true,
        _isDefault: false,
        class_name: "",
      },
    ];
  }, [defaultPrompts, customPrompts, t]);

  const currentTemplate = useMemo(() => {
    if (!selectedPrompt) return "";
    if (selectedPrompt._isDefault) {
      return selectedPrompt.metadata?.templates?.[selectedLanguage] || "";
    }
    if (selectedPrompt.parameters?.templates) {
      return selectedPrompt.parameters.templates[selectedLanguage] || "";
    }
    return selectedPrompt.parameters?.template || "";
  }, [selectedPrompt, selectedLanguage]);

  const isDefault = selectedPrompt?._isDefault;

  useEffect(() => {
    if (!selectedPrompt) {
      if (onTokenCountChange) onTokenCountChange(0);
      return;
    }

    if (
      !isInitializedRef.current &&
      promptModel?.component ===
        (selectedPrompt.class_name || selectedPrompt.name)
    ) {
      isInitializedRef.current = true;
      return;
    }
    isInitializedRef.current = true;

    setPromptModel({
      component: selectedPrompt.class_name || selectedPrompt.name,
      params: {
        template: currentTemplate,
        language: selectedLanguage,
        ...(selectedPrompt._isDefault || selectedPrompt.parameters?.templates
          ? { templates: selectedPrompt.parameters?.templates }
          : {}),
      },
    });
    if (onTokenCountChange) {
      const tokenCount = Math.ceil(currentTemplate.length / 4);
      onTokenCountChange(tokenCount);
    }
  }, [selectedPrompt, selectedLanguage]);

  useEffect(() => {
    const selectable = mergedOptions.filter((o) => !o._isCreateNew);
    if (!selectable.length) return;

    if (promptModel?.component) {
      const found = selectable.find((p) => {
        if (p._isDefault) {
          return p.class_name === promptModel.component;
        }
        return (
          p.class_name === promptModel.component &&
          p.parameters?.template === promptModel.params?.template
        );
      });
      if (found?.id !== selectedPrompt?.id) {
        setSelectedPrompt(found || null);
        prevSelectedRef.current = found || null;
        if (found?._isDefault) {
          setSelectedLanguage(promptModel.params?.language || platformLang);
        }
        isInitializedRef.current = false;
      }
      return;
    }

    if (!selectedPrompt) {
      const firstDefault =
        selectable.find((p) => p._isDefault) || selectable[0];
      if (firstDefault) {
        setSelectedPrompt(firstDefault);
        setSelectedLanguage(platformLang);
        prevSelectedRef.current = firstDefault;
      }
    }
  }, [mergedOptions, promptModel]);

  /**
   * Handles selection change in the autocomplete. Intercepts the "Create new" option
   * to open the creation modal instead of selecting it.
   * @param {object} _event - The change event.
   * @param {object|null} newValue - The newly selected option.
   */
  const handlePromptChange = (_event, newValue) => {
    if (newValue?._isCreateNew) {
      setNewPromptModalOpen(true);
      setSelectedPrompt(prevSelectedRef.current);
      return;
    }
    prevSelectedRef.current = newValue;
    setSelectedPrompt(newValue);
    if (newValue?._isDefault) {
      setSelectedLanguage(platformLang);
    }
  };

  const handleLanguageChange = (event) => {
    setSelectedLanguage(event.target.value);
  };

  /**
   * Refetches prompts after creation, selects the new prompt, and syncs state.
   * @param {number|string} newPromptId - ID of the newly created prompt.
   */
  const handlePromptCreated = useCallback(
    async (newPromptId) => {
      const updatedPrompts = await getRAGPrompts();
      setCustomPrompts(
        (updatedPrompts || []).filter(
          (p) =>
            !p.class_name.startsWith("Default") &&
            isGenerationPromptClass(p.class_name),
        ),
      );

      const newPrompt = (updatedPrompts || []).find(
        (p) => p.id === newPromptId,
      );
      if (newPrompt) {
        const wrapped = { ...newPrompt, _isDefault: false };
        setSelectedPrompt(wrapped);
        prevSelectedRef.current = wrapped;
        // Sync language from the newly created prompt's saved language
        // so local selectedLanguage stays aligned with the persisted value.
        if (newPrompt.parameters?.language) {
          setSelectedLanguage(newPrompt.parameters.language);
        }
        // Sync parent promptModel immediately to prevent infinite
        // useEffect 1 <-> useEffect 2 ping-pong when the new prompt's
        // class_name differs from the previously selected prompt.
        setPromptModel({
          component: newPrompt.class_name,
          params: {
            template: newPrompt.parameters?.template || "",
            language: newPrompt.parameters?.language || "",
          },
        });
        const template = newPrompt.parameters?.template || "";
        const tokenCount = Math.ceil(template.length / 4);
        onTokenCountChange?.(tokenCount);
      }

      setNewPromptModalOpen(false);
    },
    [onTokenCountChange, setPromptModel],
  );

  if (loading) {
    return null;
  }

  return (
    <Card sx={{ backgroundColor: "background.paper" }}>
      <CardContent sx={{ p: 2 }}>
        <Box sx={{ mb: 2 }}>
          <Box
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "space-between",
            }}
          >
            <Typography variant="subtitle2">
              {t("generative:rag.prompt.promptLabel")}
            </Typography>
            <Box>
              {isExpanded && (
                <Tooltip title={t("generative:rag.prompt.descriptionToggle")}>
                  <IconButton
                    size="small"
                    onClick={() => setShowDescription((s) => !s)}
                    aria-label="prompt-info"
                    sx={{ color: "text.secondary" }}
                  >
                    <InfoIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}
              <Tooltip title={t("generative:rag.prompt.openPrompts")}>
                <IconButton
                  size="small"
                  onClick={goToPromptsDetail}
                  aria-label="open-prompt-library"
                >
                  <ViewListIcon fontSize="small" />
                </IconButton>
              </Tooltip>
              <Tooltip
                title={
                  isExpanded
                    ? t("generative:rag.prompt.collapse")
                    : t("generative:rag.prompt.expand")
                }
              >
                <IconButton
                  size="small"
                  onClick={() => setIsExpanded((s) => !s)}
                  aria-label="toggle-prompt-card"
                >
                  <ExpandMoreIcon
                    fontSize="small"
                    sx={{
                      transform: isExpanded ? "rotate(180deg)" : "rotate(0deg)",
                      transition: "transform 0.2s",
                    }}
                  />
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
          {isExpanded && showDescription && (
            <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
              {t("generative:rag.prompt.description")}
            </Typography>
          )}
        </Box>

        <RAGSectionColumn>
          <Box>
            <Autocomplete
              options={mergedOptions}
              value={selectedPrompt}
              onChange={handlePromptChange}
              getOptionLabel={(option) => getOptionLabel(option, t)}
              isOptionEqualToValue={(option, value) => option.id === value.id}
              renderOption={(props, option) => (
                <li {...props}>{getOptionLabel(option, t)}</li>
              )}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label={t("generative:rag.prompt.selectTemplate")}
                  placeholder={t(
                    "generative:rag.prompt.selectTemplatePlaceholder",
                  )}
                />
              )}
              sx={{}}
            />
          </Box>

          {isExpanded &&
            (isDefault || selectedPrompt?.parameters?.templates) && (
              <TextField
                select
                fullWidth
                label={t("generative:rag.prompt.language")}
                value={selectedLanguage}
                onChange={handleLanguageChange}
                size="small"
              >
                {LANGUAGE_CODES.map((code) => (
                  <MenuItem key={code} value={code}>
                    {t(`generative:rag.prompt.languages.${code}`)}
                  </MenuItem>
                ))}
              </TextField>
            )}

          {isExpanded && selectedPrompt && (
            <Box>
              <Typography variant="subtitle2" sx={{ mb: 2 }}>
                {t("generative:rag.prompt.selectedTemplate")}
              </Typography>

              <Box
                sx={{
                  p: 2,
                  backgroundColor: "background.paper",
                  border: "1px solid",
                  borderColor: "divider",
                  borderRadius: 1,
                  fontFamily: theme.typography.code.fontFamily,
                  lineHeight: 1.6,
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-word",
                }}
              >
                {renderTemplateWithHighlights(
                  currentTemplate,
                  placeholderColors,
                  theme.typography.code.fontFamily,
                )}
              </Box>

              {getDescription(selectedPrompt.description, i18n) && (
                <Typography
                  variant="caption"
                  display="block"
                  sx={{ color: "text.secondary" }}
                >
                  {getDescription(selectedPrompt.description, i18n)}
                </Typography>
              )}
            </Box>
          )}

          {isExpanded && (
            <Button
              variant="contained"
              fullWidth
              color="primary"
              size="large"
              startIcon={<AddIcon />}
              onClick={() => setNewPromptModalOpen(true)}
            >
              {t("generative:rag.prompt.newPromptButton")}
            </Button>
          )}
        </RAGSectionColumn>
      </CardContent>

      <NewPromptModal
        open={newPromptModalOpen}
        handleClose={() => setNewPromptModalOpen(false)}
        onPromptCreated={handlePromptCreated}
        existingPrompts={customPrompts}
      />
    </Card>
  );
}

PromptParamsCard.propTypes = {
  promptModel: PropTypes.shape({
    component: PropTypes.string,
    params: PropTypes.shape({
      template: PropTypes.string,
      language: PropTypes.string,
    }),
  }),
  setPromptModel: PropTypes.func.isRequired,
  onTokenCountChange: PropTypes.func,
};
