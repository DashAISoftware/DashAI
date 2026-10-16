import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Alert, Button, FormControlLabel, Stack, Switch } from "@mui/material";
import { useTranslation } from "react-i18next";
import PresetCardList from "./PresetCardList";
import QueryTransformationAdvancedModal from "../../../pages/generative/RAGSession/advanced/QueryTransformationAdvancedModal";
import {
  getGeneratorComponents,
  getQueryTransformationComponents,
  getQueryTransformationPrompts,
} from "../../../api/rag";

/**
 * Reads the `llm_model` placeholder a transformer's schema declares.
 *
 * All transformation techniques share their schema, so the first component
 * carrying the placeholder carries the backend-declared default generator.
 *
 * @param {Array} transformers - The transformation components from the API.
 * @returns {string|null} The default generator name, or null when no schema
 *   declares one.
 */
export function resolveDefaultGeneratorName(transformers) {
  const declaring = (transformers || []).find(
    (component) =>
      component.schema?.properties?.llm_model?.placeholder?.component,
  );
  return declaring?.schema.properties.llm_model.placeholder.component ?? null;
}

/**
 * Resolves a component's display name or description, whether the API shipped
 * it as a localized string or as a multilingual object (legacy endpoints may
 * emit the raw object shape).
 *
 * @param {string|object|undefined} value - The multilingual or plain value.
 * @param {string} fallback - What to return when nothing resolvable is there.
 * @returns {string} A renderable plain string.
 */
export function resolveLabel(value, fallback = "") {
  if (!value) return fallback;
  if (typeof value === "string") return value;
  return value.en ?? value.es ?? fallsBackToFirstString(value, fallback);
}

/**
 * First string field of a multilingual object, or the fallback.
 * @param {object} value - A multilingual-shaped object.
 * @param {string} fallback - What to return when no field is a string.
 * @returns {string} The first string found, or the fallback.
 */
function fallsBackToFirstString(value, fallback) {
  const first = Object.values(value || {}).find(
    (candidate) => typeof candidate === "string",
  );
  return typeof first === "string" ? first : fallback;
}

/**
 * Build the `{component, params}` reference a freshly enabled stage PUTs.
 *
 * The backend fills omitted defaults server-side, but it validates that
 * `llm_model` and `prompt` are present, so both are seeded here: the
 * backend-declared default generator (the transformation schema's
 * `llm_model` placeholder, resolved against the offered list) and the
 * technique's default prompt. Everything else is left out so the server
 * supplies it.
 *
 * @param {object} transformerComponent - The transformer component to enable.
 * @param {string} technique - Its `metadata.technique`, to pick the prompt.
 * @param {object|null} firstGenerator - The generator to prefill, if any.
 * @param {Array} prompts - The transformation prompts to choose from.
 * @returns {object} The `{component, params}` session parameter value.
 */
export function buildQueryTransformationRef(
  transformerComponent,
  technique,
  firstGenerator,
  prompts,
) {
  const params = {};
  if (firstGenerator) {
    params.llm_model = { component: firstGenerator.name, params: {} };
  }
  const defaultPrompt = (prompts || []).find(
    (prompt) =>
      prompt.metadata?.technique === technique &&
      prompt.metadata?.variant === "default",
  );
  if (defaultPrompt) {
    params.prompt = {
      component: defaultPrompt.name,
      params: { language: "en" },
    };
  }
  return { component: transformerComponent.name, params };
}

/**
 * The optional query transformation stage, edited as a `{component, params}`
 * reference or `null` when disabled.
 *
 * Wears the retrieval card's shape: a technique card list over the resolution
 * API, with an advanced modal for the full reference. It owns its own option
 * loading so the panel only has to wire the section.
 *
 * @param {object}   props
 * @param {object|null} props.value - The current stage ref, or null when off.
 * @param {Function} props.onChange - Sets the stage ref, or null to disable.
 * @param {object}   [props.section] - The resolved configuration section, for
 *   the registration notice.
 * @returns {JSX.Element} The query transformation picker.
 */
export default function QueryTransformationPicker({
  value,
  onChange,
  section,
}) {
  const { t } = useTranslation(["generative"]);
  const [transformers, setTransformers] = useState([]);
  const [generators, setGenerators] = useState([]);
  const [prompts, setPrompts] = useState([]);
  const [showAdvanced, setShowAdvanced] = useState(false);

  useEffect(() => {
    getQueryTransformationComponents()
      .then((data) => setTransformers(data || []))
      .catch((error) =>
        console.error("Failed to load query transformers:", error),
      );
    getQueryTransformationPrompts()
      .then((data) => setPrompts(data || []))
      .catch((error) =>
        console.error("Failed to load query transformation prompts:", error),
      );
    getGeneratorComponents()
      .then((data) => setGenerators(data || []))
      .catch((error) =>
        console.error("Failed to load generation models:", error),
      );
  }, []);

  const enabled = value != null;

  // The generator the ref points at, else the backend-declared default (the
  // transformer schemas' `llm_model` placeholder), else the first downloaded
  // one, else the first listed: pre-selecting one is what the backend
  // requires on enable.
  const defaultGeneratorName = useMemo(
    () => resolveDefaultGeneratorName(transformers),
    [transformers],
  );
  const firstGenerator = useMemo(() => {
    const current = value?.params?.llm_model?.component;
    return (
      (current && generators.find((generator) => generator.name === current)) ||
      (defaultGeneratorName &&
        generators.find(
          (generator) => generator.name === defaultGeneratorName,
        )) ||
      generators.find((generator) => generator.downloaded) ||
      generators[0] ||
      null
    );
  }, [generators, value, defaultGeneratorName]);

  const technique = useMemo(
    () =>
      transformers.find((component) => component.name === value?.component)
        ?.metadata?.technique,
    [transformers, value?.component],
  );

  // The card list is per-technique, so a card is matched on the component
  // alone: its `params` carry server-filled defaults that always differ from
  // the `{}` a card seeds.
  const presets = useMemo(
    () =>
      transformers.map((component) => ({
        key: component.name,
        display_name: resolveLabel(component.display_name, component.name),
        description: resolveLabel(component.description),
        component: component.name,
        params: {},
      })),
    [transformers],
  );

  const enableWith = (transformer) =>
    onChange(
      buildQueryTransformationRef(
        transformer,
        transformer?.metadata?.technique,
        firstGenerator,
        prompts,
      ),
    );

  const handleSelect = (preset) => {
    const transformer =
      transformers.find((component) => component.name === preset.component) ||
      preset;
    enableWith(transformer);
  };

  // An enabled component the registry does not know about: the saved section
  // reports it unregistered, and a freshly chosen one is absent from the list.
  const unregistered =
    enabled &&
    section?.registered !== true &&
    !transformers.some((component) => component.name === value?.component);

  return (
    <Stack spacing={1.5}>
      <FormControlLabel
        control={
          <Switch
            size="small"
            checked={enabled}
            disabled={transformers.length === 0}
            onChange={(event) =>
              event.target.checked
                ? enableWith(transformers[0])
                : onChange(null)
            }
          />
        }
        label={t("generative:rag.config.queryTransformation.enable")}
      />

      <PresetCardList
        presets={presets}
        activeKey={enabled ? value?.component : null}
        onSelect={handleSelect}
      />

      {unregistered && (
        <Alert severity="info" sx={{ py: 0.5 }}>
          {value?.component}:{" "}
          {t("generative:rag.config.queryTransformation.unknownComponent")}
        </Alert>
      )}

      <Button
        variant="outlined"
        size="small"
        sx={{ alignSelf: "flex-start" }}
        disabled={!enabled}
        onClick={() => setShowAdvanced(true)}
      >
        {t("generative:rag.config.queryTransformation.advanced")}
      </Button>

      <QueryTransformationAdvancedModal
        open={showAdvanced}
        onClose={() => setShowAdvanced(false)}
        model={value}
        setModel={onChange}
        technique={technique}
        generators={generators}
        prompts={prompts}
      />
    </Stack>
  );
}

QueryTransformationPicker.propTypes = {
  value: PropTypes.object,
  onChange: PropTypes.func.isRequired,
  section: PropTypes.object,
};
