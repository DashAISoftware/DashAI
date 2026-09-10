import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Divider,
  IconButton,
  LinearProgress,
  Stack,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import SideBar from "../../threeSectionLayout/panelContainers/SideBar";
import PromptParamsCard from "./PromptParamsCard";
import GeneratorPicker from "./GeneratorPicker";
import ChunkingAdvancedModal from "../../../pages/generative/RAGSession/advanced/ChunkingAdvancedModal";
import RetrieverAdvancedModal from "../../../pages/generative/RAGSession/advanced/RetrieverAdvancedModal";
import { loadRetrieverKinds } from "../../../pages/generative/RAGSession/retrieverKinds";
import {
  getChunkingPresets,
  getRAGSession,
  getRetrieverComponents,
  getRetrieverPresets,
  getSessionConfiguration,
  updateGenerativeSessionParams,
} from "../../../api/rag";
import { updateGenerativeSession } from "../../../api/session";
import { getApiErrorMessage } from "../../../utils/apiError";

/** Section keys, matching the RAG parameter keys the backend uses. */
const SECTIONS = [
  "chunking_model",
  "retriever_model",
  "prompt",
  "generation_model",
];

/**
 * A collapsible configuration section with a backend-supplied title.
 *
 * @param {object} props
 * @param {string} props.title - Localized section name.
 * @param {string} [props.summary] - One-line current value, shown when collapsed.
 * @param {string} [props.info] - Contextual help, shown behind an info icon.
 * @param {boolean} props.expanded - Whether the section is open.
 * @param {Function} props.onToggle - Toggles the section.
 * @param {JSX.Element} props.children - The section body.
 * @returns {JSX.Element} The section.
 */
function ConfigSection({ title, summary, info, expanded, onToggle, children }) {
  return (
    <Box sx={{ borderBottom: 1, borderColor: "divider", py: 1 }}>
      <Box
        onClick={onToggle}
        sx={{
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          cursor: "pointer",
          gap: 1,
        }}
      >
        <Box sx={{ minWidth: 0 }}>
          <Stack direction="row" spacing={0.5} alignItems="center">
            <Typography variant="subtitle2">{title}</Typography>
            {info && (
              <Tooltip title={info}>
                <InfoOutlinedIcon
                  fontSize="inherit"
                  sx={{ color: "text.secondary" }}
                />
              </Tooltip>
            )}
          </Stack>
          {summary && (
            <Typography variant="caption" color="text.secondary" noWrap>
              {summary}
            </Typography>
          )}
        </Box>
        <IconButton size="small">
          <ExpandMoreIcon
            fontSize="small"
            sx={{
              transform: expanded ? "rotate(180deg)" : "rotate(0deg)",
              transition: "transform 0.2s",
            }}
          />
        </IconButton>
      </Box>
      <Collapse in={expanded} timeout="auto" unmountOnExit>
        <Box sx={{ pt: 2, pb: 1 }}>{children}</Box>
      </Collapse>
    </Box>
  );
}

ConfigSection.propTypes = {
  title: PropTypes.string.isRequired,
  summary: PropTypes.string,
  info: PropTypes.string,
  expanded: PropTypes.bool.isRequired,
  onToggle: PropTypes.func.isRequired,
  children: PropTypes.node,
};

/**
 * The single place a RAG session is configured.
 *
 * Replaces the split between a read-only summary in the centre and an editable
 * params bar on the right: every component appears once, under one name, and is
 * editable here. All labels, preset names and the context budget are resolved
 * by the backend, so this component renders rather than translates.
 *
 * @param {object}   props
 * @param {number}   props.sessionId - The RAG session being configured.
 * @param {object}   [props.indexStatus] - Current indexing state, for the
 *   re-indexing warning.
 * @param {Function} [props.onSaved] - Called after parameters are persisted.
 * @param {Function} [props.onSessionRenamed] - Called with the new name.
 * @returns {JSX.Element} The configuration panel.
 */
export default function RAGConfigPanel({
  sessionId,
  indexStatus,
  onSaved,
  onSessionRenamed,
}) {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();

  const [configuration, setConfiguration] = useState(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [expanded, setExpanded] = useState({});

  // Editable working copy of the parameters, seeded from the session.
  const [draft, setDraft] = useState(null);
  const [savedDraft, setSavedDraft] = useState(null);
  const [modelAvailable, setModelAvailable] = useState(true);

  const [chunkingPresets, setChunkingPresets] = useState([]);
  const [retrieverPresets, setRetrieverPresets] = useState([]);
  const [retrieverComponents, setRetrieverComponents] = useState([]);
  const [showChunkingAdvanced, setShowChunkingAdvanced] = useState(false);
  const [showRetrieverAdvanced, setShowRetrieverAdvanced] = useState(false);

  const [editingMetadata, setEditingMetadata] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");

  const load = useCallback(async () => {
    if (!sessionId) return;
    setLoading(true);
    try {
      const [session, resolved] = await Promise.all([
        getRAGSession(sessionId),
        getSessionConfiguration(sessionId),
      ]);
      const parameters = session.parameters || {};
      const next = {
        chunking_model: parameters.chunking_model || {
          component: "",
          params: {},
        },
        retriever_model: parameters.retriever_model || {
          component: "",
          params: {},
        },
        prompt: parameters.prompt || { component: "", params: {} },
        generation_model: parameters.generation_model || {
          component: "",
          params: {},
        },
      };
      setDraft(next);
      setSavedDraft(next);
      setConfiguration(resolved);
      setName(session.name || "");
      setDescription(session.description || "");
    } catch (error) {
      console.error("Failed to load RAG configuration:", error);
      enqueueSnackbar(t("generative:rag.paramsPanel.failedToLoad"), {
        variant: "error",
      });
    } finally {
      setLoading(false);
    }
  }, [sessionId, enqueueSnackbar, t]);

  useEffect(() => {
    load();
  }, [load]);

  // Preset recipes come resolved from the backend; the Top-K currently in use
  // keeps the retriever recipes comparable with what the session already has.
  useEffect(() => {
    getChunkingPresets()
      .then(setChunkingPresets)
      .catch((error) =>
        console.error("Failed to load chunking presets:", error),
      );
  }, []);

  // The advanced retriever builder needs the full component list, and its
  // grouping needs the retriever taxonomy the backend exposes.
  useEffect(() => {
    loadRetrieverKinds()
      .then(() => getRetrieverComponents("RetrieverModel"))
      .then(setRetrieverComponents)
      .catch((error) =>
        console.error("Failed to load retriever components:", error),
      );
  }, []);

  const topK = configuration?.retriever_model?.top_k;
  useEffect(() => {
    getRetrieverPresets(topK || 10)
      .then(setRetrieverPresets)
      .catch((error) =>
        console.error("Failed to load retriever presets:", error),
      );
  }, [topK]);

  const dirty = useMemo(
    () => JSON.stringify(draft) !== JSON.stringify(savedDraft),
    [draft, savedDraft],
  );

  const updateSection = useCallback((key, value) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }, []);

  const toggleSection = (key) =>
    setExpanded((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleSave = async () => {
    if (!dirty || saving) return;
    setSaving(true);
    try {
      await updateGenerativeSessionParams(sessionId, draft);
      setSavedDraft(draft);
      const resolved = await getSessionConfiguration(sessionId);
      setConfiguration(resolved);
      enqueueSnackbar(t("generative:rag.paramsPanel.updated"), {
        variant: "success",
      });
      onSaved?.();
    } catch (error) {
      console.error("Failed to update RAG session:", error);
      enqueueSnackbar(
        getApiErrorMessage(
          error,
          t("generative:rag.paramsPanel.failedToUpdate"),
        ),
        { variant: "error" },
      );
    } finally {
      setSaving(false);
    }
  };

  const handleSaveMetadata = async () => {
    const trimmed = name.trim();
    if (!trimmed) {
      enqueueSnackbar(t("generative:rag.validation.nameRequired"), {
        variant: "error",
      });
      return;
    }
    try {
      await updateGenerativeSession({
        id: String(sessionId),
        formData: { name: trimmed, description },
      });
      setEditingMetadata(false);
      onSessionRenamed?.(trimmed);
      enqueueSnackbar(t("generative:rag.summary.sessionUpdated"), {
        variant: "success",
      });
    } catch (error) {
      console.error("Failed to update session metadata:", error);
      enqueueSnackbar(t("generative:rag.summary.failedToUpdateSession"), {
        variant: "error",
      });
    }
  };

  if (loading || !configuration || !draft) {
    return (
      <SideBar>
        <Box sx={{ display: "flex", justifyContent: "center", p: 4 }}>
          <CircularProgress />
        </Box>
      </SideBar>
    );
  }

  const budget = configuration.context_budget;
  const budgetUsed =
    budget.context_window > 0
      ? Math.min(
          100,
          Math.round(
            ((budget.context_window - budget.available) /
              budget.context_window) *
              100,
          ),
        )
      : 0;

  /**
   * The preset recipe the unsaved draft currently matches, if any.
   *
   * Clicking a chip applies that recipe verbatim, so an exact comparison
   * against the recipe is enough to keep the panel in step with the draft — no
   * waiting for a save round-trip, and no domain knowledge here.
   *
   * @param {string} key - The configuration section key.
   * @param {Array} presets - The preset recipes for that section.
   * @returns {object|null} The matching recipe, or null for a custom config.
   */
  const matchedPreset = (key, presets) => {
    const ref = draft[key];
    return (
      presets.find(
        (preset) =>
          preset.component === ref?.component &&
          JSON.stringify(preset.params) === JSON.stringify(ref?.params),
      ) ?? null
    );
  };

  /**
   * Which preset key is active for a section.
   * @param {string} key - The configuration section key.
   * @param {Array} presets - The preset recipes for that section.
   * @returns {string|null} The active preset key, or null for a custom config.
   */
  const activePresetKey = (key, presets) => {
    const match = matchedPreset(key, presets);
    if (match) return match.key;
    return dirty ? null : configuration[key].preset_key;
  };

  /**
   * One-line description of a section, shown while it is collapsed.
   *
   * Prefers the preset the *draft* matches so an unsaved change is reflected
   * right away; falls back to the backend's resolved answer otherwise.
   *
   * @param {string} key - The configuration section key.
   * @returns {string} The summary line.
   */
  const sectionSummary = (key) => {
    const section = configuration[key];
    if (!section) return "";

    if (key === "chunking_model") {
      const preset = matchedPreset(key, chunkingPresets);
      if (preset) {
        return [preset.display_name, preset.description]
          .filter(Boolean)
          .join(" · ");
      }
      return [section.preset_display_name, section.summary]
        .filter(Boolean)
        .join(" · ");
    }

    if (key === "retriever_model") {
      const preset = matchedPreset(key, retrieverPresets);
      const label =
        preset?.display_name ||
        section.preset_display_name ||
        section.display_name;
      return [
        label,
        section.top_k
          ? t("generative:rag.config.chunkCount", { count: section.top_k })
          : null,
      ]
        .filter(Boolean)
        .join(" · ");
    }

    return section.display_name || "";
  };

  const sectionBody = (key) => {
    if (key === "chunking_model") {
      const active = activePresetKey("chunking_model", chunkingPresets);
      return (
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {chunkingPresets.map((preset) => (
              <Chip
                key={preset.key}
                label={preset.display_name}
                size="small"
                color={active === preset.key ? "primary" : "default"}
                variant={active === preset.key ? "filled" : "outlined"}
                onClick={() =>
                  updateSection("chunking_model", {
                    component: preset.component,
                    params: preset.params,
                  })
                }
              />
            ))}
          </Stack>
          <Button
            variant="outlined"
            size="small"
            sx={{ alignSelf: "flex-start" }}
            onClick={() => setShowChunkingAdvanced(true)}
          >
            {t("generative:rag.config.advanced")}
          </Button>
          <ChunkingAdvancedModal
            open={showChunkingAdvanced}
            onClose={() => setShowChunkingAdvanced(false)}
            chunkingModel={draft.chunking_model}
            setChunkingModel={(value) => updateSection("chunking_model", value)}
          />
        </Stack>
      );
    }

    if (key === "retriever_model") {
      const active = activePresetKey("retriever_model", retrieverPresets);
      return (
        <Stack spacing={1.5}>
          <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
            {retrieverPresets.map((preset) => (
              <Chip
                key={preset.key}
                label={preset.display_name}
                size="small"
                color={active === preset.key ? "primary" : "default"}
                variant={active === preset.key ? "filled" : "outlined"}
                onClick={() =>
                  updateSection("retriever_model", {
                    component: preset.component,
                    params: preset.params,
                  })
                }
              />
            ))}
          </Stack>
          <Button
            variant="outlined"
            size="small"
            sx={{ alignSelf: "flex-start" }}
            onClick={() => setShowRetrieverAdvanced(true)}
          >
            {t("generative:rag.config.advanced")}
          </Button>
          <RetrieverAdvancedModal
            open={showRetrieverAdvanced}
            onClose={() => setShowRetrieverAdvanced(false)}
            selectedParadigm={null}
            allParadigms={retrieverComponents}
            retrieverModel={draft.retriever_model}
            setRetrieverModel={(value) =>
              updateSection("retriever_model", value)
            }
          />
        </Stack>
      );
    }

    if (key === "prompt") {
      return (
        <PromptParamsCard
          promptModel={draft.prompt}
          setPromptModel={(value) => updateSection("prompt", value)}
          onTokenCountChange={() => {}}
        />
      );
    }

    return (
      <GeneratorPicker
        generatorModel={draft.generation_model}
        setGeneratorModel={(value) => updateSection("generation_model", value)}
        onAvailabilityChange={setModelAvailable}
      />
    );
  };

  return (
    <SideBar>
      <Box
        sx={{
          p: 2,
          height: "100%",
          display: "flex",
          flexDirection: "column",
          gap: 1,
        }}
      >
        {/* Session identity */}
        {editingMetadata ? (
          <Stack spacing={1}>
            <TextField
              size="small"
              label={t("generative:rag.summary.sessionName")}
              value={name}
              onChange={(event) => setName(event.target.value)}
            />
            <TextField
              size="small"
              multiline
              rows={2}
              label={t("generative:rag.summary.sessionDescription")}
              value={description}
              onChange={(event) => setDescription(event.target.value)}
            />
            <Stack direction="row" spacing={1} justifyContent="flex-end">
              <Button size="small" onClick={() => setEditingMetadata(false)}>
                {t("generative:rag.summary.cancel")}
              </Button>
              <Button
                size="small"
                variant="contained"
                onClick={handleSaveMetadata}
              >
                {t("generative:rag.summary.save")}
              </Button>
            </Stack>
          </Stack>
        ) : (
          <Stack direction="row" alignItems="center" spacing={0.5}>
            <Typography variant="h6" noWrap sx={{ flex: 1, minWidth: 0 }}>
              {name}
            </Typography>
            <IconButton
              size="small"
              onClick={() => setEditingMetadata(true)}
              aria-label={t("generative:rag.summary.edit")}
            >
              <EditIcon fontSize="small" />
            </IconButton>
          </Stack>
        )}

        {indexStatus?.status === "stale" && (
          <Alert severity="warning" sx={{ py: 0.5 }}>
            {indexStatus.message}
          </Alert>
        )}

        <Divider />

        <Box sx={{ flex: 1, overflowY: "auto", minHeight: 0 }}>
          {SECTIONS.map((key) => (
            <ConfigSection
              key={key}
              title={configuration[key].section_name}
              summary={sectionSummary(key)}
              info={configuration[key].description || undefined}
              expanded={Boolean(expanded[key])}
              onToggle={() => toggleSection(key)}
            >
              {sectionBody(key)}
            </ConfigSection>
          ))}

          {/* Context budget, computed by the backend from the live config. */}
          <Box sx={{ pt: 2 }}>
            <Typography variant="subtitle2">
              {t("generative:rag.config.contextBudget")}
            </Typography>
            <LinearProgress
              variant="determinate"
              value={budgetUsed}
              color={budget.is_valid ? "primary" : "error"}
              sx={{ my: 1, borderRadius: 1, height: 6 }}
            />
            <Typography variant="caption" color="text.secondary">
              {t("generative:validation.contextSpace", {
                availableChars: budget.available.toLocaleString(),
              })}
            </Typography>
            {!budget.is_valid && (
              <Alert severity="error" sx={{ mt: 1, py: 0.5 }}>
                {t("generative:validation.insufficientContextDescription")}
              </Alert>
            )}
          </Box>
        </Box>

        <Divider />
        <Box sx={{ display: "flex", justifyContent: "flex-end", pt: 1 }}>
          <Button
            variant="contained"
            size="small"
            onClick={handleSave}
            disabled={!dirty || saving || !modelAvailable}
          >
            {t("generative:rag.paramsPanel.save")}
          </Button>
        </Box>
      </Box>
    </SideBar>
  );
}

RAGConfigPanel.propTypes = {
  sessionId: PropTypes.oneOfType([PropTypes.number, PropTypes.string])
    .isRequired,
  indexStatus: PropTypes.object,
  onSaved: PropTypes.func,
  onSessionRenamed: PropTypes.func,
};
