/* eslint-disable react/prop-types */
import { Stack } from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useModelSchemaStore } from "../../contexts/schema";
import ModelSchemaBreadScrumbs from "./ModelSchemaBreadScrumbs";
import ModelSchemaForm from "./ModelSchemaForm";
import ModelSchemaSelect from "./ModelSchemaSelect";

// eslint-disable-next-line react/prop-types
function FormSchemaWithSelectedModel({
  // eslint-disable-next-line react/prop-types
  modelToConfigure,
  initialValues,
  onFormSubmit,
  onCancel,
}) {
  const {
    formValues,
    properties,
    propertyData,
    valuesByProperties,
    removeLastProperty,
  } = useModelSchemaStore();

  const [selectedModel, setSelectedModel] = useState(propertyData?.model);

  const selectedProperty = Boolean(propertyData?.selected);

  const defaultValues = useMemo(() => {
    if (selectedProperty) {
      if (selectedModel === propertyData.model) {
        return propertyData.params;
      } else return null;
    }

    return initialValues ?? valuesByProperties;
  }, [selectedModel, propertyData.params]);

  useEffect(() => {
    setSelectedModel(propertyData.model);
  }, [propertyData.model, propertyData.params]);

  return (
    <Stack spacing={4} sx={{ py: 2 }}>
      {/* Dropdown to select a configurable object to render a subform */}

      {Boolean(propertyData) && (
        <>
          <ModelSchemaBreadScrumbs properties={properties} />
          <ModelSchemaSelect
            parent={propertyData.parent}
            selectedModel={selectedModel}
            onChange={setSelectedModel}
          />
        </>
      )}

      <ModelSchemaForm
        model={selectedModel}
        initialValues={defaultValues}
        onFormSubmit={() => onFormSubmit(formValues)}
        onCancel={() => {
          if (properties.length > 0) {
            removeLastProperty();
          } else {
            onCancel();
          }
        }}
      />
    </Stack>
  );
}

export default FormSchemaWithSelectedModel;
