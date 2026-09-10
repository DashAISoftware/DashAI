import { Box, Switch, TextField, Typography } from "@mui/material";
import PropTypes from "prop-types";
import { useCallback, useEffect, useRef, useState } from "react";
import { useTheme } from "@mui/material/styles";
import FormSchema from "../../shared/FormSchema";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import FormInputWrapper from "../../configurableObject/Inputs/FormInputWrapper";
import InputWithDebounce from "../../shared/InputWithDebounce";
import { generateSequentialName } from "../../../utils/nameGenerator";
import FormSchemaFieldCard from "../../shared/FormSchemaFieldCard";
import { useTranslation } from "react-i18next";
import SideBar from "../../threeSectionLayout/panelContainers/SideBar";
import { getComponents as getComponentsRequest } from "../../../api/component";

/**
 * Right sidebar component for configuring dataloader parameters
 * Similar to ParamsBar in Generative section
 *
 * @param {string} selectedDataloader - The dataloader type to configure
 * @param {object} formSubmitRef - The reference to the form submit function
 * @param {function} setError - The function to set the error state
 * @param {array} existingDatasets - Array of existing datasets to avoid name conflicts
 * @param {function} onValuesChange - Callback function called when form values change
 */
export default function DataloaderConfigBar({
  selectedDataloader,
  formSubmitRef,
  setError,
  onValuesChange,
  computeMetadata = true,
  onComputeMetadataChange,
}) {
  const [inferenceRows, setInferenceRows] = useState(1000);
  const [supportsNativeTypes, setSupportsNativeTypes] = useState(false);
  const [useNativeTypes, setUseNativeTypes] = useState(false);
  const schemaValuesRef = useRef({});
  const { t } = useTranslation(["common", "datasets"]);
  const theme = useTheme();
  const showInferenceRows = selectedDataloader !== "ImageDataLoader";

  useEffect(() => {
    let cancelled = false;
    setUseNativeTypes(false);
    if (!selectedDataloader) {
      setSupportsNativeTypes(false);
      return () => {
        cancelled = true;
      };
    }
    getComponentsRequest({ model: selectedDataloader })
      .then((components) => {
        if (cancelled) return;
        const component = Array.isArray(components)
          ? components[0]
          : components;
        const flag = !!component?.metadata?.supports_native_types;
        setSupportsNativeTypes(flag);
        if (flag) {
          setUseNativeTypes(true);
          if (onValuesChange) {
            onValuesChange({
              ...schemaValuesRef.current,
              inference_rows: inferenceRows,
              use_native_types: true,
            });
          }
        }
      })
      .catch(() => {
        if (!cancelled) setSupportsNativeTypes(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedDataloader]);

  // Handler for when FormSchema values change - merge with inference_rows + native flag
  const handleFormSchemaValuesChange = useCallback(() => {
    const values = formSubmitRef?.current?.values || {};
    schemaValuesRef.current = values;
    if (onValuesChange) {
      onValuesChange({
        ...values,
        inference_rows: inferenceRows,
        use_native_types: useNativeTypes,
      });
    }
  }, [formSubmitRef, inferenceRows, useNativeTypes, onValuesChange]);

  // Handler for when inference_rows changes - merge with schema values
  const handleInferenceRowsChange = useCallback(
    (val) => {
      const numeric = val ? Math.max(2, Number(val)) : 2;
      setInferenceRows(numeric);
      if (onValuesChange) {
        onValuesChange({
          ...schemaValuesRef.current,
          inference_rows: numeric,
          use_native_types: useNativeTypes,
        });
      }
    },
    [onValuesChange, useNativeTypes],
  );

  const handleUseNativeTypesChange = useCallback(
    (event) => {
      const next = event.target.checked;
      setUseNativeTypes(next);
      if (onValuesChange) {
        onValuesChange({
          ...schemaValuesRef.current,
          inference_rows: inferenceRows,
          use_native_types: next,
        });
      }
    },
    [onValuesChange, inferenceRows],
  );

  // compute_metadata is intentionally NOT pushed through onValuesChange / formValues —
  // it flows to the parent through onComputeMetadataChange directly. Avoiding the
  // formValues round-trip keeps the preview table from re-rendering when the
  // toggle is clicked, which matters for datasets with many columns.
  const handleComputeMetadataChange = useCallback(
    (event) => {
      if (onComputeMetadataChange) {
        onComputeMetadataChange(event.target.checked);
      }
    },
    [onComputeMetadataChange],
  );

  if (!selectedDataloader) {
    return (
      <Box
        display="flex"
        height="100%"
        width="100%"
        flexDirection="column"
        justifyContent="center"
        alignItems="center"
        bgcolor="background.box"
        borderBottom={`0.1px solid ${(theme) => theme.palette.divider}`}
        p={6}
      >
        <Typography
          variant="body2"
          sx={{ color: "text.secondary", textAlign: "center" }}
        >
          {t("datasets:label.selectDataloaderToConfigure")}
        </Typography>
      </Box>
    );
  }

  return (
    <SideBar data-tour="dataloader-config">
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          height: 64,
          display: "flex",
          alignItems: "center",
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("datasets:label.dataloaderConfiguration")}
        </Typography>
      </Box>

      <Box sx={{ flex: 1, overflowY: "auto", px: 4, pt: 2, pb: 4 }}>
        {showInferenceRows && (
          <Box
            sx={{
              pb: 2,
            }}
          >
            {supportsNativeTypes && (
              <Box sx={{ pb: 2 }}>
                <FormSchemaFieldCard
                  label={t("datasets:label.useNativeTypes")}
                  description={t("datasets:label.useNativeTypesDescription")}
                >
                  <Box sx={{ pt: 2 }}>
                    <Switch
                      checked={useNativeTypes}
                      onChange={handleUseNativeTypesChange}
                      size="small"
                      name="use_native_types"
                    />
                  </Box>
                </FormSchemaFieldCard>
              </Box>
            )}
            <Box sx={{ pb: 2 }}>
              <FormSchemaFieldCard
                label={t("datasets:computeMetadata.label")}
                description={t("datasets:computeMetadata.helper")}
              >
                <Box sx={{ pt: 2 }}>
                  <Switch
                    checked={computeMetadata}
                    onChange={handleComputeMetadataChange}
                    size="small"
                    name="compute_metadata"
                  />
                </Box>
              </FormSchemaFieldCard>
            </Box>
            <FormSchemaFieldCard
              label={t(
                useNativeTypes
                  ? "datasets:label.previewRows"
                  : "datasets:label.inferenceRows",
              )}
              description={t(
                useNativeTypes
                  ? "datasets:label.previewRowsDescription"
                  : "datasets:label.inferenceRowsDescription",
              )}
            >
              <Box sx={{ pt: 2 }}>
                <InputWithDebounce
                  name="inference_rows"
                  value={inferenceRows}
                  onChange={handleInferenceRowsChange}
                  type="number"
                  variant="outlined"
                  size="small"
                  fullWidth
                  slotProps={{ input: { min: 2 } }}
                />
              </Box>
            </FormSchemaFieldCard>
          </Box>
        )}
        <FormSchemaContainer>
          <FormSchema
            autoSave
            model={selectedDataloader}
            formSubmitRef={formSubmitRef}
            setError={setError}
            initialValues={{}}
            onValuesChange={handleFormSchemaValuesChange}
            showBorder={false}
          />
        </FormSchemaContainer>
      </Box>
    </SideBar>
  );
}

DataloaderConfigBar.propTypes = {
  selectedDataloader: PropTypes.string,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }),
  setError: PropTypes.func,
  onValuesChange: PropTypes.func,
  computeMetadata: PropTypes.bool,
  onComputeMetadataChange: PropTypes.func,
};
