import React, { useState, useEffect, useMemo } from "react";
import { Box, Autocomplete, TextField, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { getChunkingComponents } from "../../../../api/rag";
import FormSchema from "../../../../components/shared/FormSchema";
import FormSchemaContainer from "../../../../components/shared/FormSchemaContainer";
import {
  resolveDefaults,
  getModelFromSubform,
  getParamsFromSubform,
} from "../../../../utils/schema";

/**
 * Step component for selecting a chunking strategy and configuring its parameters.
 * Includes validation that chunk_overlap is less than chunk_size.
 *
 * @param {object} props
 * @param {object} [props.chunkingModel] - The current chunking model { component, params }.
 * @param {function} props.setChunkingModel - State setter for the chunking model.
 * @param {function} [props.setNextEnabled] - Callback to enable/disable the next button.
 * @returns {JSX.Element} The chunking configuration step UI.
 */
export default function ChunkingConfigurationStep({
  chunkingModel,
  setChunkingModel,
  setNextEnabled,
}) {
  const { t } = useTranslation(["generative"]);
  const [chunkingOptions, setChunkingOptions] = useState([]);
  const [selectedChunking, setSelectedChunking] = useState(null);
  const [error, setError] = useState(null);

  const [fetchedDefaults, setFetchedDefaults] = useState(null);

  useEffect(() => {
    if (!selectedChunking) return;
    let cancelled = false;
    (async () => {
      const d = await resolveDefaults(selectedChunking.name);
      if (!cancelled) setFetchedDefaults(d);
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedChunking]);

  const formInitialValues = useMemo(() => {
    if (selectedChunking) {
      const existingModelName = getModelFromSubform(chunkingModel);
      const existingParams =
        getParamsFromSubform(chunkingModel) ?? chunkingModel?.params;
      if (
        existingModelName === selectedChunking.name &&
        existingParams &&
        Object.keys(existingParams).length > 0
      ) {
        return existingParams;
      }
    }
    return fetchedDefaults || {};
  }, [selectedChunking, chunkingModel, fetchedDefaults]);

  useEffect(() => {
    let isMounted = true;
    const fetchChunkingModels = async () => {
      const data = await getChunkingComponents();
      if (isMounted) {
        setChunkingOptions(data || []);
        console.log("[ChunkingConfigStep] Fetched chunking options:", data);
      }
    };
    fetchChunkingModels();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!chunkingOptions.length) return;
    const modelName = getModelFromSubform(chunkingModel);
    console.log("[ChunkingConfigStep] Syncing selectedChunking:", {
      modelName,
      chunkingModel,
      chunkingOptions: chunkingOptions.map((c) => c.name),
    });
    if (modelName) {
      const found = chunkingOptions.find((c) => c.name === modelName);
      if (found) {
        console.log("[ChunkingConfigStep] Found chunking model:", found.name);
        setSelectedChunking(found);
        setNextEnabled(true);
      }
    } else {
      setNextEnabled(false);
    }
  }, [chunkingOptions, chunkingModel]);

  /**
   * Handles selection of a chunking component from the autocomplete.
   * Resolves default parameters and updates the chunking model.
   * @param {object} event - The autocomplete change event.
   * @param {object|null} newValue - The selected chunking component.
   */
  const handleChunkingSelectionChange = async (event, newValue) => {
    setSelectedChunking(newValue);
    setError(null);

    if (newValue) {
      const defaults = await resolveDefaults(newValue.name);
      setChunkingModel({
        component: newValue.name,
        params: defaults,
      });
      setNextEnabled(true);
    } else {
      setChunkingModel({ component: "", params: {} });
      setNextEnabled(false);
    }
  };

  /**
   * Persists chunking parameter values after validating overlap < size constraint.
   * Sets form-level error and disables next if validation fails.
   * @param {object} values - The form values from the schema.
   */
  const handleFormSubmit = (values) => {
    if (
      values.chunk_size !== undefined &&
      values.chunk_overlap !== undefined &&
      values.chunk_overlap >= values.chunk_size
    ) {
      const errorMsg =
        "chunk_overlap must be less than chunk_size. " +
        `Got chunk_overlap=${values.chunk_overlap} and chunk_size=${values.chunk_size}`;
      setError(errorMsg);
      setNextEnabled(false);
      return;
    }

    setError(null);
    setChunkingModel({
      component: selectedChunking.name,
      params: values,
    });
    setNextEnabled(true);
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="subtitle2" sx={{ mb: 0 }}>
        {t("generative:rag.chunkingConfig.configureTitle")}
      </Typography>

      <Autocomplete
        disablePortal
        options={chunkingOptions}
        getOptionLabel={(option) => option.name}
        value={selectedChunking}
        onChange={handleChunkingSelectionChange}
        isOptionEqualToValue={(option, value) => option.name === value?.name}
        renderInput={(params) => (
          <TextField
            {...params}
            label={t("generative:rag.chunkingConfig.modelLabel")}
          />
        )}
      />

      {error && (
        <Typography variant="body2" color="error" sx={{ px: 1 }}>
          {error}
        </Typography>
      )}

      {selectedChunking && (
        <FormSchemaContainer key={`chunking-form-${selectedChunking.name}`}>
          <FormSchema
            autoSave
            model={selectedChunking.name}
            initialValues={formInitialValues}
            onFormSubmit={handleFormSubmit}
            setError={(err) => {
              if (err) {
                console.error("FormSchema error:", err);
                setError(err?.message || "Validation error");
                setNextEnabled(false);
              }
            }}
            hideButtons
          />
        </FormSchemaContainer>
      )}
    </Box>
  );
}

ChunkingConfigurationStep.propTypes = {
  chunkingModel: PropTypes.object,
  setChunkingModel: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func,
};
