import { useEffect, useMemo, useState } from "react";
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

/** Languages the default transformation prompts can render instructions in. */
const LANGUAGES = ["en", "es", "pt"];

/**
 * Full-reference editor for the query transformation stage.
 *
 * Mirrors `RetrieverAdvancedModal`'s dialog conventions, but edits a plain
 * `{component, params}` reference field by field — the parameters are too few
 * and cross-dependent to feed through a generated schema form. The option
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
