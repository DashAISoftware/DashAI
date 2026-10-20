import { useState, useEffect, useMemo, useRef } from "react";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  IconButton,
  Autocomplete,
  TextField,
  Typography,
  Box,
  Divider,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import FormSchema from "../../../../components/shared/FormSchema";
import FormSchemaContainer from "../../../../components/shared/FormSchemaContainer";
import { resolveRetrieverDefaults } from "./resolveRetrieverDefaults";
import {
  loadRetrieverKinds,
  isComposite as isCompositeKind,
  isEmbedding as isEmbeddingKind,
} from "../retrieverKinds";

/**
 * Dialog for configuring a single node in the composite retriever tree.
 * Allows selecting a retriever component and editing its parameters.
 *
 * @param {object} props
 * @param {boolean} props.open - Whether the dialog is open.
 * @param {string} props.nodeId - The target tree node ID.
 * @param {object} [props.nodeData] - The current node data (component + params).
 * @param {Array} props.allComponents - All available retriever paradigms.
 * @param {object} props.leafRegistry - Map of leaf paradigm names to their concrete component arrays.
 * @param {function} props.onSave - Callback with (nodeId, component, params).
 * @param {function} props.onClose - Callback to close the dialog.
 * @returns {JSX.Element} The configuration dialog.
 */
export default function RetrieverNodeConfig({
  open,
  nodeId,
  nodeData,
  allComponents,
  leafRegistry,
  onSave,
  onClose,
}) {
  const { t } = useTranslation(["generative"]);
  const [kindsLoaded, setKindsLoaded] = useState(false);

  const allOptions = useMemo(() => {
    const list = [...allComponents];
    for (const key of Object.keys(leafRegistry)) {
      if (!isEmbeddingKind(key)) {
        list.push(...(leafRegistry[key] || []));
      }
    }
    const seen = new Set();
    return list
      .filter((c) => c.configurable_object !== false)
      .filter((c) => {
        if (seen.has(c.name)) return false;
        seen.add(c.name);
        return true;
      });
  }, [allComponents, leafRegistry, kindsLoaded]);

  const [selectedModel, setSelectedModel] = useState(null);
  const [params, setParams] = useState({});
  const [initialParams, setInitialParams] = useState({});
  // Resolving a component's defaults is asynchronous. Saving while they are
  // still loading would persist an empty or previous component's payload, so
  // the Save action waits for the requested component's defaults.
  const [loadingDefaults, setLoadingDefaults] = useState(false);
  const defaultsRequestRef = useRef(0);

  useEffect(() => {
    loadRetrieverKinds().then(() => setKindsLoaded(true));
  }, []);

  useEffect(() => {
    if (!nodeData || !allOptions.length) return;
    const found = allOptions.find((c) => c.name === nodeData.component);
    setSelectedModel(found || null);
    const p = nodeData.params || {};
    setParams(p);
    setInitialParams(p);
  }, [nodeData, allOptions]);

  const isComposite = selectedModel && isCompositeKind(selectedModel.name);

  /**
   * Resolves the display name from a component's display_name (string or multilingual object).
   * @param {object} opt - The component option object.
   * @returns {string} The resolved display name.
   */
  const getDisplay = (opt) => {
    if (!opt) return "";
    const dn = opt.display_name;
    if (!dn) return opt.name || "";
    if (typeof dn === "string") return dn;
    if (dn.en) return dn.en;
    if (dn.es) return dn.es;
    const keys = Object.keys(dn);
    for (const key of keys) {
      if (typeof dn[key] === "string") return dn[key];
    }
    return opt.name || "";
  };

  /**
   * Handles selection of a new retriever component and loads its default
   * parameters. Only the latest request may write the form state, so quickly
   * switching components cannot apply a stale response.
   * @param {object} _e - The autocomplete event.
   * @param {object|null} newVal - The newly selected component option.
   */
  const handleModelChange = async (_e, newVal) => {
    const requestId = defaultsRequestRef.current + 1;
    defaultsRequestRef.current = requestId;
    setSelectedModel(newVal);

    if (!newVal) {
      setParams({});
      setLoadingDefaults(false);
      return;
    }

    setLoadingDefaults(true);
    try {
      const defaults = await resolveRetrieverDefaults(newVal.name);
      if (requestId !== defaultsRequestRef.current) return;
      setParams(defaults);
      setInitialParams(defaults);
    } finally {
      if (requestId === defaultsRequestRef.current) {
        setLoadingDefaults(false);
      }
    }
  };

  /**
   * Saves the current component selection and parameters.
   */
  const handleSave = () => {
    if (!selectedModel) return;
    onSave(nodeId, selectedModel.name, params);
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle
        sx={{
          bgcolor: "background.paper",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
        }}
      >
        {t("generative:rag.composite.configureNode")}
        <IconButton
          onClick={onClose}
          size="small"
          sx={{ color: "text.secondary" }}
        >
          <CloseIcon />
        </IconButton>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 3 }}>
          <Autocomplete
            options={allOptions}
            value={selectedModel}
            onChange={handleModelChange}
            getOptionLabel={(opt) => getDisplay(opt)}
            isOptionEqualToValue={(a, b) => a.name === b.name}
            groupBy={(opt) => {
              if (isCompositeKind(opt.name))
                return t("generative:rag.composite.compositeGroup");
              return t("generative:rag.composite.simpleGroup");
            }}
            renderInput={(p) => (
              <TextField
                {...p}
                label={t("generative:rag.composite.selectModel")}
              />
            )}
          />

          {isComposite && (
            <Typography variant="caption" color="text.secondary">
              {t("generative:rag.composite.nestedCompositeNote")}
            </Typography>
          )}

          {selectedModel && (
            <>
              <Divider />
              <Typography variant="subtitle2">
                {t("generative:rag.composite.parameters")}
              </Typography>
              <FormSchemaContainer
                key={`node-config-${nodeId}-${selectedModel.name}`}
              >
                <FormSchema
                  model={selectedModel.name}
                  initialValues={initialParams}
                  autoSave
                  onFormSubmit={(values) => setParams(values)}
                  hideButtons
                  excludeFields={isComposite ? ["children"] : []}
                />
              </FormSchemaContainer>
            </>
          )}
        </Box>
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button onClick={onClose} variant="outlined">
          {t("common:cancel")}
        </Button>
        <Button
          onClick={handleSave}
          variant="contained"
          disabled={!selectedModel || loadingDefaults}
        >
          {t("common:save")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

RetrieverNodeConfig.propTypes = {
  open: PropTypes.bool.isRequired,
  nodeId: PropTypes.string.isRequired,
  nodeData: PropTypes.object,
  allComponents: PropTypes.array.isRequired,
  leafRegistry: PropTypes.object.isRequired,
  onSave: PropTypes.func.isRequired,
  onClose: PropTypes.func.isRequired,
};
