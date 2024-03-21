/* eslint-disable react/prop-types */
import { Box, Stack, Typography } from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useModelSchemaStore } from "../../contexts/schema";
import ModelSchemaForm from "./ModelSchemaForm";
import ModelSchemaSelect from "./ModelSchemaSelect";

// eslint-disable-next-line react/prop-types
function ModelSchema({
  // eslint-disable-next-line react/prop-types
  modelToConfigure,
  onFormSubmit,
  onClose,
  initialValues,
}) {
  const {
    properties,
    propertyData,
    valuesByProperties,
    handleUpdateValues,
    removeLastProperty,
  } = useModelSchemaStore();

  const [selectedModel, setSelectedModel] = useState(propertyData?.model);

  const selectedProperty = Boolean(propertyData?.selected);
  const handleOnCancel = () => {
    if (!selectedProperty) {
      onClose();
    } else {
      removeLastProperty();
    }
  };

  const handleOnSubmit = (values) => {
    if (!selectedProperty) {
      handleUpdateValues(values, onFormSubmit);
      return;
    }
    const formattedValues = {
      properties: {
        component: propertyData.parent,
        params: {
          comp: {
            component: selectedModel,
            params: values,
          },
        },
      },
    };

    handleUpdateValues(formattedValues);
  };

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
          <Box display="flex">
            {properties.map((property, index) => (
              <Typography variant="overline" key={property.key}>
                {`${property.label}/` + " "}
              </Typography>
            ))}
          </Box>

          <ModelSchemaSelect
            parent={propertyData.parent}
            selectedModel={selectedModel}
            onChange={setSelectedModel}
          />
        </>
      )}

      <ModelSchemaForm
        model={selectedModel}
        onFormSubmit={handleOnSubmit}
        initialValues={defaultValues}
        onCancel={handleOnCancel}
      />
    </Stack>
  );
}

export default ModelSchema;
