import {
  useState,
  useEffect,
  useCallback,
  useRef,
  useMemo,
  forwardRef,
  useImperativeHandle,
} from "react";
import PropTypes from "prop-types";
import { Box, Autocomplete, TextField, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import { getRetrievalParadigm } from "../../../../api/rag";
import {
  loadRetrieverKinds,
  isComposite as isCompositeKind,
  retrieverCategory,
  sortByCategory,
} from "../retrieverKinds";
import FormSchema from "../../../../components/shared/FormSchema";
import CompositeRetrieverBuilder from "./CompositeRetrieverBuilder";
import { FormSchemaProvider } from "../../../../contexts/schema";
import { resolveDefaults } from "../../../../utils/schema";

/**
 * Resolves a component's display name from its display_name field (string or multilingual).
 * @param {object} component - The component definition object.
 * @returns {string} The resolved display name or the component name as fallback.
 */
function getDisplayName(component) {
  if (!component) return "";
  const dn = component.display_name;
  if (!dn) return component.name || "";
  if (typeof dn === "string") return dn;
  if (dn.en) return dn.en;
  if (dn.es) return dn.es;
  // Fallback: try any available language key
  const keys = Object.keys(dn);
  for (const key of keys) {
    if (typeof dn[key] === "string") return dn[key];
  }
  return component.name || "";
}

/**
 * Auto-saving form wrapper around FormSchema for retriever parameter configuration.
 * Loads default values for the selected retriever and fires onParametersChange on edits.
 *
 * @param {object} props
 * @param {object} props.selectedRetriever - The currently selected retriever component.
 * @param {object} [props.retrieverModel] - The persisted retriever model { component, params }.
 * @param {function} props.onParametersChange - Callback with the latest parameter values.
 * @returns {JSX.Element} The auto-saving schema form.
 */
function AutoSaveFormSchema({
  selectedRetriever,
  retrieverModel,
  onParametersChange,
}) {
  const formikRef = useRef(null);

  const [fetchedDefaults, setFetchedDefaults] = useState(null);

  useEffect(() => {
    if (!selectedRetriever) return;
    let cancelled = false;
    (async () => {
      const d = await resolveDefaults(selectedRetriever.name);
      if (!cancelled) setFetchedDefaults(d);
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedRetriever]);

  const initialValues = useMemo(() => {
    if (
      retrieverModel?.component === selectedRetriever?.name &&
      retrieverModel?.params &&
      Object.keys(retrieverModel.params).length > 0
    ) {
      return retrieverModel.params;
    }
    return fetchedDefaults || {};
  }, [selectedRetriever, retrieverModel, fetchedDefaults]);

  const handleFormSubmit = useCallback(
    (values) => {
      onParametersChange(values);
    },
    [onParametersChange],
  );

  return (
    <FormSchema
      model={selectedRetriever.name}
      initialValues={initialValues}
      autoSave={true}
      onFormSubmit={handleFormSubmit}
      formSubmitRef={formikRef}
      hideButtons
    />
  );
}

/**
 * Step component for selecting and configuring a retriever (simple, dense embedding,
 * or composite). Exposes a `saveFormValues` imperative handle for parent dialogs.
 *
 * @param {object} props
 * @param {Array} [props.allParadigms] - All available retriever paradigms.
 * @param {object} [props.retrieverModel] - The current retriever model { component, params }.
 * @param {function} props.setRetrieverModel - State setter for the retriever model.
 * @param {function} props.setNextEnabled - Callback to enable/disable the next/submit button.
 * @param {object} ref - React ref for imperative handle (saveFormValues).
 * @returns {JSX.Element} The retriever configuration step UI.
 */
const RetrieverConfigurationStep = forwardRef(
  function RetrieverConfigurationStep(
    { allParadigms, retrieverModel, setRetrieverModel, setNextEnabled },
    ref,
  ) {
    const { t } = useTranslation(["generative", "common"]);
    const [allOptions, setAllOptions] = useState([]);
    const [selectedRetriever, setSelectedRetriever] = useState(null);
    const [openConfig, setOpenConfig] = useState(false);
    const savedParamsRef = useRef(null);

    /**
     * Persists the current form parameter values into the retriever model state.
     * Used by parent dialogs via the imperative ref handle.
     */
    const saveCurrentFormValues = useCallback(() => {
      const values = savedParamsRef.current;
      if (values && Object.keys(values).length > 0 && selectedRetriever) {
        setRetrieverModel({
          component: selectedRetriever.name,
          params: values,
        });
      }
    }, [selectedRetriever, setRetrieverModel]);

    useEffect(() => {
      return () => {
        saveCurrentFormValues();
      };
    }, [saveCurrentFormValues]);

    useImperativeHandle(
      ref,
      () => ({ saveFormValues: saveCurrentFormValues }),
      [saveCurrentFormValues],
    );

    useEffect(() => {
      const load = async () => {
        await loadRetrieverKinds();
        let retrievers = [];
        try {
          retrievers = await getRetrievalParadigm();
        } catch (e) {
          retrievers = allParadigms || [];
        }
        const options = sortByCategory(
          (retrievers || []).filter(
            (retriever) => retriever.configurable_object !== false,
          ),
          t("common:other"),
        );
        setAllOptions(options);

        if (retrieverModel?.component) {
          const found =
            options.find((c) => c.name === retrieverModel.component) ||
            allParadigms?.find((c) => c.name === retrieverModel.component) ||
            null;
          if (found) {
            setSelectedRetriever(found);
            setOpenConfig(true);
            setNextEnabled(true);
          }
        }
      };
      load();
    }, []);

    /**
     * Handles selection of a new retriever from the autocomplete and resets
     * its parameters to the retriever's defaults.
     * @param {object} _event - The autocomplete event.
     * @param {object|null} newValue - The selected retriever option.
     */
    const handleRetrieverChange = useCallback(
      async (_event, newValue) => {
        savedParamsRef.current = null;

        if (!newValue) {
          setSelectedRetriever(null);
          setRetrieverModel({ component: "", params: {} });
          setOpenConfig(false);
          setNextEnabled(false);
          return;
        }

        const defaults = await resolveDefaults(newValue.name);
        setSelectedRetriever(newValue);
        setRetrieverModel({ component: newValue.name, params: defaults });
        setOpenConfig(Boolean(newValue?.schema?.properties));
        setNextEnabled(true);
      },
      [setRetrieverModel, setNextEnabled],
    );

    /**
     * Stores updated parameter values from the auto-saving form into the retriever model.
     * @param {object} newParams - The latest parameter values from the form.
     */
    const handleParametersSave = useCallback(
      (newParams) => {
        savedParamsRef.current = newParams;
        setRetrieverModel({
          component: selectedRetriever?.name || "",
          params: newParams,
        });
        setNextEnabled(true);
      },
      [selectedRetriever?.name, setRetrieverModel, setNextEnabled],
    );

    /**
     * Receives the serialised tree from CompositeRetrieverBuilder and persists it
     * into the retriever model.
     * @param {object} updated - The updated composite model { component, params }.
     */
    const handleCompositeChange = useCallback(
      (updated) => {
        savedParamsRef.current = updated.params;
        setRetrieverModel({
          component: updated.component,
          params: updated.params,
        });
        setNextEnabled(true);
      },
      [setRetrieverModel, setNextEnabled],
    );

    const isComposite =
      selectedRetriever && isCompositeKind(selectedRetriever.name);

    return (
      <Box sx={{ display: "flex", flexDirection: "column", gap: 3, p: 2 }}>
        <Typography variant="subtitle2" sx={{ mb: 0 }}>
          {t("generative:rag.composite.selectModel")}
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
          {t("generative:rag.composite.retrieverDescription")}
        </Typography>
        <Autocomplete
          options={allOptions}
          getOptionLabel={(opt) => getDisplayName(opt)}
          groupBy={(opt) => retrieverCategory(opt, t("common:other"))}
          value={selectedRetriever}
          onChange={handleRetrieverChange}
          isOptionEqualToValue={(a, b) => a.name === b.name}
          renderInput={(params) => (
            <TextField
              {...params}
              label={t("generative:rag.retrieverConfig.modelLabel")}
            />
          )}
        />

        {selectedRetriever && openConfig && !isComposite && (
          <FormSchemaProvider
            key={`retriever-provider-${selectedRetriever.name}`}
          >
            <AutoSaveFormSchema
              key={`retriever-form-${selectedRetriever.name}`}
              selectedRetriever={selectedRetriever}
              retrieverModel={retrieverModel}
              onParametersChange={handleParametersSave}
            />
          </FormSchemaProvider>
        )}

        {selectedRetriever && openConfig && isComposite && (
          <>
            <Typography variant="body2" color="text.secondary" sx={{ mt: -1 }}>
              {t("generative:rag.composite.compositeInstructions")}
            </Typography>
            <CompositeRetrieverBuilder
              key={`composite-${selectedRetriever.name}`}
              rootComponent={selectedRetriever.name}
              rootParams={retrieverModel.params}
              onChange={handleCompositeChange}
            />
          </>
        )}
      </Box>
    );
  },
);

RetrieverConfigurationStep.propTypes = {
  allParadigms: PropTypes.array,
  retrieverModel: PropTypes.object,
  setRetrieverModel: PropTypes.func.isRequired,
  setNextEnabled: PropTypes.func.isRequired,
};

export default RetrieverConfigurationStep;
