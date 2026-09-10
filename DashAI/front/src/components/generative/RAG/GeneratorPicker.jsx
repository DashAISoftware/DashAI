import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import { useTranslation } from "react-i18next";
import ComponentDownloadControl from "../../models/model/ComponentDownloadControl";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../../credentials/credentialStatus";
import GeneratorAdvancedModal from "../../../pages/generative/RAGSession/advanced/GeneratorAdvancedModal";
import { getGeneratorComponents } from "../../../api/rag";
import { resolveDefaults } from "../../../utils/schema";

/**
 * The single generation-model picker used across the RAG UI.
 *
 * Shows every model under one name and one label, and surfaces the download
 * and credential state that the components API already reports — so a model
 * that cannot be used says so here instead of failing on save.
 *
 * @param {object}   props
 * @param {object}   props.generatorModel - Current `{ component, params }`.
 * @param {Function} props.setGeneratorModel - Sets the generator configuration.
 * @param {Function} [props.onAvailabilityChange] - Reports whether the selected
 *   model can actually be used (downloaded and credentials satisfied).
 * @returns {JSX.Element} The generator picker.
 */
export default function GeneratorPicker({
  generatorModel,
  setGeneratorModel,
  onAvailabilityChange,
}) {
  const { t } = useTranslation(["generative"]);
  const [generators, setGenerators] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const { statuses, loaded: credentialsLoaded } = useCredentialStatuses();

  useEffect(() => {
    let cancelled = false;
    getGeneratorComponents()
      .then((data) => {
        if (!cancelled) setGenerators(data || []);
      })
      .catch((error) => {
        console.error("Error loading generation models:", error);
      })
      .finally(() => {
        if (!cancelled) setLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const selected = useMemo(
    () =>
      generators.find(
        (generator) => generator.name === generatorModel?.component,
      ) ?? null,
    [generators, generatorModel?.component],
  );

  const needsDownload =
    Boolean(selected?.metadata?.requires_download) && !selected?.downloaded;
  const { locked, requiredPlatforms } = getComponentCredentialState(
    selected || {},
    statuses,
    credentialsLoaded,
  );

  // Nothing is reported while the list is still in flight: without it there is
  // no `selected` to judge, and a panel that mounts and unmounts this picker
  // before the response lands would keep that premature "unavailable" after
  // the picker is gone, leaving its save button dead with nothing explaining
  // why.
  useEffect(() => {
    if (loading) return;
    onAvailabilityChange?.(Boolean(selected) && !needsDownload && !locked);
  }, [loading, selected, needsDownload, locked, onAvailabilityChange]);

  /**
   * Select a model and seed it with the parameters its schema declares.
   * @param {object} _event - Autocomplete change event (unused).
   * @param {object|null} option - The chosen model component.
   */
  const handleChange = async (_event, option) => {
    if (!option) {
      setGeneratorModel({ component: "", params: {} });
      return;
    }
    const params = await resolveDefaults(option.name);
    setGeneratorModel({ component: option.name, params });
  };

  /**
   * Reflect an inline download in the local list so the warning clears at once.
   * @param {boolean} isDownloaded - The model's new download state.
   */
  const handleDownloadChange = (isDownloaded) => {
    setGenerators((prev) =>
      prev.map((generator) =>
        generator.name === selected?.name
          ? { ...generator, downloaded: isDownloaded }
          : generator,
      ),
    );
  };

  if (loading) return null;

  return (
    <Stack spacing={2}>
      <Autocomplete
        options={generators}
        value={selected}
        onChange={handleChange}
        getOptionLabel={(option) => option.display_name || option.name || ""}
        isOptionEqualToValue={(option, value) => option?.name === value?.name}
        renderInput={(params) => (
          <TextField
            {...params}
            size="small"
            label={t("generative:rag.generator.selectModel")}
          />
        )}
      />

      {selected?.description && (
        <Typography variant="caption" color="text.secondary">
          {selected.description}
        </Typography>
      )}

      {selected && needsDownload && (
        <Alert severity="warning" sx={{ py: 0.5 }}>
          {t("generative:rag.generator.downloadRequired")}
        </Alert>
      )}

      {selected && (
        <Box>
          <ComponentDownloadControl
            component={selected}
            onStatusChange={handleDownloadChange}
          />
        </Box>
      )}

      {selected && locked && (
        <Alert severity="warning" sx={{ py: 0.5 }}>
          {t("generative:validation.apiKeyMissingDescription")}
          {requiredPlatforms ? ` (${requiredPlatforms})` : ""}
        </Alert>
      )}

      <Button
        variant="outlined"
        size="small"
        disabled={!selected}
        onClick={() => setShowAdvanced(true)}
        sx={{ alignSelf: "flex-start" }}
      >
        {t("generative:rag.generator.advancedButton")}
      </Button>

      {selected && (
        <GeneratorAdvancedModal
          open={showAdvanced}
          onClose={() => setShowAdvanced(false)}
          selectedGenerator={selected}
          generatorModel={generatorModel}
          setGeneratorModel={setGeneratorModel}
        />
      )}
    </Stack>
  );
}

GeneratorPicker.propTypes = {
  generatorModel: PropTypes.object,
  setGeneratorModel: PropTypes.func.isRequired,
  onAvailabilityChange: PropTypes.func,
};
