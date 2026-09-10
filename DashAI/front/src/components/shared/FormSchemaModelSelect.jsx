import { Box, FormControl, MenuItem } from "@mui/material";
import React from "react";
import useModelParents from "../../hooks/useModelParents";
import { Input } from "../configurableObject/Inputs/InputStyles";
import { useFormSchemaStore } from "../../contexts/schema";
import {
  formattedModel,
  formattedSubform,
  generateYupSchema,
} from "../../utils/schema";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import ComponentDownloadControl from "../models/model/ComponentDownloadControl";

/**
 * This component is a select input for the models of a parent model
 * @param {string} parent - The parent model
 * @param {string} selectedModel - The selected model
 * @param {function} onChange - The function to update the selected model
 */

function FormSchemaModelSelect({ parent, selectedModel, onChange }) {
  const { models, markDownloaded } = useModelParents({ parent });
  const { handleUpdateSchema } = useFormSchemaStore();
  const { t } = useTranslation(["common"]);

  if (!models || !selectedModel) {
    return null;
  }

  const selectedComponent = models.find(
    (model) => model.name === selectedModel,
  );

  const handleOnChange = async (event) => {
    const model = models.find((model) => model.name === event.target.value);
    const { initialValues } = generateYupSchema(
      await formattedModel(model.schema),
    );
    handleUpdateSchema(
      formattedSubform({ parent, model: model.name, params: initialValues }),
    );
    onChange(event.target.value);
  };

  return (
    <FormControl sx={{ width: "auto" }}>
      <Input
        select
        label={t("common:selectModel")}
        value={selectedModel}
        onChange={handleOnChange}
      >
        {models?.map((model) => (
          <MenuItem key={model.name} value={model.name}>
            {model.name}
          </MenuItem>
        ))}
      </Input>
      {selectedComponent?.metadata?.requires_download && (
        <Box sx={{ mt: 1 }}>
          <ComponentDownloadControl
            component={selectedComponent}
            onStatusChange={(isDownloaded) =>
              markDownloaded(selectedComponent.name, isDownloaded)
            }
          />
        </Box>
      )}
    </FormControl>
  );
}

FormSchemaModelSelect.propTypes = {
  parent: PropTypes.string.isRequired,
  selectedModel: PropTypes.string.isRequired,
  onChange: PropTypes.func.isRequired,
};

export default FormSchemaModelSelect;
