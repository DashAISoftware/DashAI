import { useState, useEffect, useMemo } from "react";
import PropTypes from "prop-types";
import { Box, Autocomplete, TextField, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import FormSchema from "../../../../components/shared/FormSchema";
import FormSchemaContainer from "../../../../components/shared/FormSchemaContainer";
import { getGeneratorComponents } from "../../../../api/rag";
import { resolveDefaults } from "../../../../utils/schema";

/**
 * Step component for selecting a generator (LLM) and configuring its parameters.
 *
 * @param {object} props
 * @param {object} [props.generatorModel] - The current generator model { component, params }.
 * @param {function} props.setGeneratorModel - State setter for the generator model.
 * @param {function} [props.setNextEnabled] - Callback to enable/disable the next button.
 * @returns {JSX.Element} The generator configuration step UI.
 */
export default function GeneratorConfigurationStep({
  generatorModel,
  setGeneratorModel,
  setNextEnabled,
}) {
  const { t } = useTranslation(["generative"]);
  const [generators, setGenerators] = useState([]);
  const [selectedGenerator, setSelectedGenerator] = useState(null);

  const [fetchedDefaults, setFetchedDefaults] = useState(null);

  useEffect(() => {
    if (!selectedGenerator) return;
    let cancelled = false;
    (async () => {
      const d = await resolveDefaults(selectedGenerator.name);
      if (!cancelled) setFetchedDefaults(d);
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedGenerator]);

  const formInitialValues = useMemo(() => {
    if (
      generatorModel?.component === selectedGenerator?.name &&
      generatorModel?.params &&
      Object.keys(generatorModel.params).length > 0
    ) {
      return generatorModel.params;
    }
    return fetchedDefaults || {};
  }, [
    selectedGenerator,
    generatorModel?.component,
    generatorModel?.params,
    fetchedDefaults,
  ]);

  useEffect(() => {
    let isMounted = true;
    const load = async () => {
      const data = await getGeneratorComponents();
      if (isMounted) setGenerators(data || []);
    };
    load();
    return () => {
      isMounted = false;
    };
  }, []);

  useEffect(() => {
    if (!generators.length) return;
    if (generatorModel?.component) {
      const found = generators.find((g) => g.name === generatorModel.component);
      if (found) setSelectedGenerator(found);
    }
    setNextEnabled(!!generatorModel?.component);
  }, [generators, generatorModel?.component]);

  /**
   * Handles selection of a generator component from the autocomplete.
   * Resolves default parameters and updates the generator model.
   * @param {object} event - The autocomplete change event.
   * @param {object|null} newValue - The selected generator component.
   */
  const handleSelection = async (event, newValue) => {
    setSelectedGenerator(newValue);
    if (newValue) {
      const defaults = await resolveDefaults(newValue.name);
      setGeneratorModel({
        component: newValue.name,
        params: defaults,
      });
      setNextEnabled(true);
    } else {
      setGeneratorModel({ component: "", params: {} });
      setNextEnabled(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
      <Typography variant="subtitle2" sx={{ mb: 0 }}>
        {t("generative:rag.generatorConfig.configureTitle")}
      </Typography>

      <Autocomplete
        disablePortal
        options={generators}
        getOptionLabel={(option) => option.name}
        value={selectedGenerator}
        onChange={handleSelection}
        isOptionEqualToValue={(option, value) => option.name === value?.name}
        renderInput={(params) => (
          <TextField
            {...params}
            label={t("generative:rag.generatorConfig.modelLabel")}
          />
        )}
      />

      {selectedGenerator && (
        <FormSchemaContainer key={`generator-form-${selectedGenerator.name}`}>
          <FormSchema
            autoSave
            model={selectedGenerator.name}
            initialValues={formInitialValues}
            onFormSubmit={(values) => {
              setGeneratorModel({
                component: selectedGenerator.name,
                params: values,
              });
            }}
            setError={(err) => console.error("FormSchema error:", err)}
            hideButtons
          />
        </FormSchemaContainer>
      )}
    </Box>
  );
}

GeneratorConfigurationStep.propTypes = {
  generatorModel: PropTypes.object,
  setGeneratorModel: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func,
};
