import { useCallback, useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import {
  Alert,
  Box,
  Button,
  CircularProgress,
  Divider,
  IconButton,
  LinearProgress,
  Stack,
  Tab,
  TextField,
  Tooltip,
  Typography,
} from "@mui/material";
import EditIcon from "@mui/icons-material/Edit";
import FiberManualRecordIcon from "@mui/icons-material/FiberManualRecord";
import InfoOutlinedIcon from "@mui/icons-material/InfoOutlined";
import SideBar from "../../threeSectionLayout/panelContainers/SideBar";
import PillTabs from "../../shared/PillTabs";
import PresetCardList from "./PresetCardList";
import PromptEditor from "./PromptEditor";
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

/**
 * Section keys, matching the RAG parameter keys the backend uses, in the order
 * the pipeline applies them: split the documents, retrieve from them, answer
 * with a model, phrase it with a prompt.
 */
const SECTIONS = [
  "chunking_model",
  "retriever_model",
  "generation_model",
  "prompt",
];

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
  const [activeSection, setActiveSection] = useState(SECTIONS[0]);
  const [promptValid, setPromptValid] = useState(true);

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

  // Which sections hold unsaved edits. One Save still sends the whole draft --
  // the endpoint replaces every parameter at once -- but with the sections
  // behind tabs a pending change is otherwise invisible from another tab.
  const dirtySections = useMemo(() => {
    if (!draft || !savedDraft) return [];
    return SECTIONS.filter(
      (key) => JSON.stringify(draft[key]) !== JSON.stringify(savedDraft[key]),
    );
  }, [draft, savedDraft]);

  const updateSection = useCallback((key, value) => {
    setDraft((prev) => ({ ...prev, [key]: value }));
  }, []);

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

  const handleDiscard = () => setDraft(savedDraft);

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
      return (
        <Stack spacing={1.5}>
          <PresetCardList
            presets={chunkingPresets}
            activeKey={activePresetKey("chunking_model", chunkingPresets)}
            onSelect={(preset) =>
              updateSection("chunking_model", {
                component: preset.component,
                params: preset.params,
              })
            }
          />
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
      return (
        <Stack spacing={1.5}>
          <PresetCardList
            presets={retrieverPresets}
            activeKey={activePresetKey("retriever_model", retrieverPresets)}
            onSelect={(preset) =>
              updateSection("retriever_model", {
                component: preset.component,
                params: preset.params,
              })
            }
          />
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
        <PromptEditor
          promptModel={draft.prompt}
          setPromptModel={(value) => updateSection("prompt", value)}
          onValidityChange={setPromptValid}
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

        {/* Scrollable, and never full width: the panel is 15-40% of the
            viewport and the labels come from the backend, so a fixed-width tab
            row would wrap. */}
        <PillTabs
          value={activeSection}
          onChange={(_event, value) => setActiveSection(value)}
          variant="scrollable"
          scrollButtons="auto"
          minHeight={36}
          sx={{ "& .MuiTab-root": { minWidth: 0, px: 1.5 } }}
        >
          {SECTIONS.map((key) => (
            <Tab
              key={key}
              value={key}
              sx={
                key === "prompt" && !promptValid
                  ? { color: "error.main" }
                  : undefined
              }
              label={
                <Stack direction="row" alignItems="center" spacing={0.5}>
                  <span>{configuration[key].section_name}</span>
                  {dirtySections.includes(key) && (
                    <FiberManualRecordIcon
                      sx={{ fontSize: 8 }}
                      color="warning"
                    />
                  )}
                </Stack>
              }
            />
          ))}
        </PillTabs>

        <Box sx={{ flex: 1, overflowY: "auto", minHeight: 0, pt: 2 }}>
          {/* Every section stays mounted, hidden rather than unrendered: the
              generator reports whether its model is usable through a callback,
              so a tab the user never opens would leave Save enabled for a
              model that cannot run. */}
          {SECTIONS.map((key) => (
            <Box key={key} hidden={key !== activeSection}>
              <Stack
                direction="row"
                spacing={0.5}
                alignItems="center"
                sx={{ mb: 1 }}
              >
                <Typography variant="caption" color="text.secondary" noWrap>
                  {sectionSummary(key)}
                </Typography>
                {configuration[key].description && (
                  <Tooltip title={configuration[key].description}>
                    <InfoOutlinedIcon
                      fontSize="inherit"
                      sx={{ color: "text.secondary" }}
                    />
                  </Tooltip>
                )}
              </Stack>
              {sectionBody(key)}
            </Box>
          ))}
        </Box>

        <Divider />

        {/* Context budget, computed by the backend from the live config. Every
            section feeds into it, so it belongs beside Save rather than at the
            end of one tab. */}
        <Box sx={{ pt: 1 }}>
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

        {dirtySections.some((key) => key !== activeSection) && (
          <Typography variant="caption" color="warning.main">
            {t("generative:rag.config.unsavedIn", {
              sections: dirtySections
                .map((key) => configuration[key].section_name)
                .join(", "),
            })}
          </Typography>
        )}

        <Box
          sx={{
            display: "flex",
            justifyContent: "flex-end",
            gap: 1,
            pt: 1,
          }}
        >
          <Button size="small" onClick={handleDiscard} disabled={!dirty}>
            {t("generative:rag.config.discard")}
          </Button>
          <Button
            variant="contained"
            size="small"
            onClick={handleSave}
            disabled={!dirty || saving || !modelAvailable || !promptValid}
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
