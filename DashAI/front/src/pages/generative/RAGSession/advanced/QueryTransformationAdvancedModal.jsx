import { useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import {
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import { useTranslation } from "react-i18next";
import { resolveLabel } from "../../../../components/generative/RAG/QueryTransformationPicker";
import FormSchema from "../../../../components/shared/FormSchema";
import FormSchemaContainer from "../../../../components/shared/FormSchemaContainer";
import { resolveDefaults } from "../../../../utils/schema";

/** Languages the default transformation prompts can render instructions in. */
const LANGUAGES = ["en", "es", "pt"];

/**
 * Decide which of the transformation LLM's parameter values a form submission
 * must persist.
 *
 * The stage's nested LLM params are merged backend-side as
 * `{...schema_defaults, ...overrides, ...caller_params}`, where `overrides`
 * pins a `context_window` larger than the schema's placeholder. So the form
 * must only ever send the keys the user actually meant to set:
 *
 *  - A cleared field is dropped, so the backend re-resolves it.
 *  - A key that was already in the carried ref is always echoed, even when it
 *    equals the schema default: it is a user choice this edit must not lose.
 *  - Any other key still equal to its schema placeholder is left out, so a
 *    freshly enabled stage does not smuggle the 512 placeholder over the
 *    backend's 2048 override.
 *
 * @param {object} carriedParams The ref's params captured when the form was
 *   seeded, i.e. what the user had stored before this edit.
 * @param {object} seedDefaults The schema's placeholder defaults.
 * @param {object} values The complete values FormSchema hands back.
 * @returns {object} The params to persist for `llm_model`.
 */
function llmParamsToPersist(carriedParams, seedDefaults, values) {
  const carried = carriedParams || {};
  const seed = seedDefaults || {};
  const result = {};

  for (const key of Object.keys(values)) {
    const value = values[key];
    if (value === "" || value === null || value === undefined) continue;

    const wasCarried = Object.prototype.hasOwnProperty.call(carried, key);
    const isUntouchedDefault =
      JSON.stringify(value) === JSON.stringify(seed[key]);
    if (!wasCarried && isUntouchedDefault) continue;

    result[key] = value;
  }

  return result;
}

/**
 * Full-reference editor for the query transformation stage.
 *
 * Mirrors `RetrieverAdvancedModal`'s dialog conventions. The nested LLM's
 * parameters are rendered from the backend schema by `FormSchema`, exactly like
 * the generator's advanced configuration, so no parameter is hand-rolled and
 * every field the schema declares stays in sync with the server. The option
 * lists are loaded by the picker and passed down, so this stays presentational.
 *
 * @param {object}   props
 * @param {boolean}  props.open - Whether the dialog is open.
 * @param {Function} props.onClose - Closes the dialog.
 * @param {object}   props.model - The current stage ref `{component, params}`.
 * @param {Function} props.setModel - Persists the edited ref.
 * @param {string}   [props.technique] - The transformer's technique, deciding
 *   which parameters apply.
 * @param {Array}    [props.generators] - Generator models for the model select.
 * @param {Array}    [props.prompts] - Transformation prompts for the prompt
 *   select.
 * @returns {JSX.Element} The advanced query transformation modal.
 */
export default function QueryTransformationAdvancedModal({
  open,
  onClose,
  model,
  setModel,
  technique,
  generators,
  prompts,
}) {
  const { t } = useTranslation(["generative"]);
  const [params, setParams] = useState(model?.params || {});
  const [seededCarried, setSeededCarried] = useState(null);
  const [seedDefaults, setSeedDefaults] = useState(null);

  // Refs mirror the seed state so the submit handler never reads a stale
  // closure: autosave rewrites `params` on every keystroke, but the carried
  // baseline must stay whatever it was when the form mounted.
  const carriedParamsRef = useRef({});
  const seedDefaultsRef = useRef({});

  // Start from the persisted reference each time the dialog opens; while it is
  // open the edits live here and only reach the session on Done.
  useEffect(() => {
    if (open) setParams(model?.params || {});
  }, [open, model]);

  const promptOptions = useMemo(
    () =>
      (prompts || []).filter(
        (prompt) =>
          prompt.metadata?.variant === "default" &&
          (!technique || prompt.metadata?.technique === technique),
      ),
    [prompts, technique],
  );

  /** Sets a scalar parameter, dropping it when cleared so the server can fill it. */
  const setScalar = (key, value) =>
    setParams((prev) => {
      const next = { ...prev };
      if (value === "" || value === null || value === undefined) {
        delete next[key];
      } else {
        next[key] = value;
      }
      return next;
    });

  /** Points a nested component parameter at `name`, keeping its params on reselect. */
  const setComponent = (key, name, emptyParams) =>
    setParams((prev) => {
      const next = { ...prev };
      if (!name) {
        delete next[key];
        return next;
      }
      next[key] = {
        component: name,
        params:
          prev[key]?.component === name
            ? prev[key].params
            : { ...(emptyParams || {}) },
      };
      return next;
    });

  const llmComponent = params.llm_model?.component;

  // Seed the schema form for the selected LLM. What the ref carried at this
  // instant decides the emission mode for the whole editing session: an empty
  // map means the backend must keep re-resolving the defaults it owns. The
  // baseline is read from the `model` prop (the pre-edit source of truth) and
  // re-captured on every dialog open, so a previously saved empty ref can
  // never be misremembered as a carried one.
  useEffect(() => {
    if (!llmComponent) {
      carriedParamsRef.current = {};
      seedDefaultsRef.current = {};
      setSeededCarried(null);
      setSeedDefaults(null);
      return undefined;
    }

    const carried = model?.params?.llm_model?.params || {};
    carriedParamsRef.current = carried;
    seedDefaultsRef.current = {};
    setSeededCarried(carried);
    setSeedDefaults(null);

    let cancelled = false;
    resolveDefaults(llmComponent).then((defaults) => {
      if (cancelled) return;
      const resolved = defaults || {};
      seedDefaultsRef.current = resolved;
      setSeedDefaults(resolved);
    });

    return () => {
      cancelled = true;
    };
    // Keyed on the open flag, the model prop and the component only: the
    // carried baseline is captured here, so it must not re-run when autosave
    // rewrites the modal's live params.
  }, [open, model, llmComponent]);

  const hasCarriedParams = Boolean(
    seededCarried && Object.keys(seededCarried).length > 0,
  );

  // Prefer the ref's own values when it carried any (so a saved
  // context_window is never lost); otherwise the schema placeholders. The form
  // waits for those defaults so the first render already shows real values.
  const llmInitialValues = useMemo(() => {
    if (!llmComponent) return {};
    if (hasCarriedParams) return params.llm_model?.params || {};
    return seedDefaults || {};
  }, [llmComponent, hasCarriedParams, params.llm_model?.params, seedDefaults]);

  const llmFormReady =
    Boolean(llmComponent) && (hasCarriedParams || seedDefaults !== null);

  /** Maps the schema form's full value set onto the params to persist. */
  const handleLlmFormSubmit = (values) =>
    setParams((prev) => {
      if (!prev.llm_model) return prev;
      return {
        ...prev,
        llm_model: {
          component: prev.llm_model.component,
          params: llmParamsToPersist(
            carriedParamsRef.current,
            seedDefaultsRef.current,
            values,
          ),
        },
      };
    });

  const handleDone = () => {
    setModel({ component: model?.component, params });
    onClose();
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{ sx: { minHeight: "400px" } }}
    >
      <DialogTitle
        sx={{
          bgcolor: "background.paper",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {t("generative:rag.config.queryTransformation.advanced")}
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ color: "text.secondary" }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Stack spacing={2} sx={{ pt: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {model?.component}
          </Typography>

          <TextField
            select
            size="small"
            label={t("generative:rag.config.queryTransformation.llm")}
            value={params.llm_model?.component || ""}
            onChange={(event) => setComponent("llm_model", event.target.value)}
          >
            {(generators || []).map((generator) => (
              <MenuItem key={generator.name} value={generator.name}>
                {resolveLabel(generator.display_name, generator.name)}
              </MenuItem>
            ))}
          </TextField>

          {llmFormReady && (
            <FormSchemaContainer key={`llm-form-${llmComponent}`}>
              <FormSchema
                autoSave
                hideButtons
                model={llmComponent}
                initialValues={llmInitialValues}
                onFormSubmit={handleLlmFormSubmit}
              />
            </FormSchemaContainer>
          )}

          <TextField
            select
            size="small"
            label={t("generative:rag.config.queryTransformation.prompt")}
            value={params.prompt?.component || ""}
            onChange={(event) =>
              setComponent("prompt", event.target.value, { language: "en" })
            }
          >
            {promptOptions.map((prompt) => (
              <MenuItem key={prompt.name} value={prompt.name}>
                {resolveLabel(prompt.display_name, prompt.name)}
              </MenuItem>
            ))}
          </TextField>

          {params.prompt?.component && (
            <TextField
              select
              size="small"
              label={t("generative:rag.config.queryTransformation.language")}
              value={params.prompt?.params?.language || "en"}
              onChange={(event) =>
                setParams((prev) =>
                  prev.prompt
                    ? {
                        ...prev,
                        prompt: {
                          ...prev.prompt,
                          params: {
                            ...prev.prompt.params,
                            language: event.target.value,
                          },
                        },
                      }
                    : prev,
                )
              }
            >
              {LANGUAGES.map((language) => (
                <MenuItem key={language} value={language}>
                  {language}
                </MenuItem>
              ))}
            </TextField>
          )}

          <TextField
            size="small"
            type="number"
            label={t("generative:rag.config.queryTransformation.historyWindow")}
            placeholder="2"
            value={params.history_window ?? ""}
            inputProps={{ min: 0 }}
            onChange={(event) =>
              setScalar(
                "history_window",
                event.target.value === "" ? "" : Number(event.target.value),
              )
            }
          />

          {technique === "expansion" && (
            <TextField
              size="small"
              type="number"
              label={t("generative:rag.config.queryTransformation.nQueries")}
              placeholder="3"
              value={params.n_queries ?? ""}
              inputProps={{ min: 1 }}
              onChange={(event) =>
                setScalar(
                  "n_queries",
                  event.target.value === "" ? "" : Number(event.target.value),
                )
              }
            />
          )}

          {technique === "decomposition" && (
            <TextField
              size="small"
              type="number"
              label={t(
                "generative:rag.config.queryTransformation.maxSubqueries",
              )}
              value={params.max_subqueries ?? ""}
              inputProps={{ min: 1 }}
              onChange={(event) =>
                setScalar(
                  "max_subqueries",
                  event.target.value === "" ? "" : Number(event.target.value),
                )
              }
            />
          )}
        </Stack>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button onClick={onClose} variant="outlined">
          {t("generative:rag.advanced.close")}
        </Button>
        <Button onClick={handleDone} variant="contained" color="primary">
          {t("generative:rag.advanced.done")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

QueryTransformationAdvancedModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  model: PropTypes.object,
  setModel: PropTypes.func.isRequired,
  technique: PropTypes.string,
  generators: PropTypes.array,
  prompts: PropTypes.array,
};
