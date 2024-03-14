/* eslint-disable react/prop-types */
import { Stack, Typography } from "@mui/material";
import React, { useEffect, useMemo, useState } from "react";
import { useModelSchemaStore } from "../../contexts/schema";
import ModelSchemaForm from "./ModelSchemaForm";
import ModelSchemaSelect from "./ModelSchemaSelect";

// eslint-disable-next-line react/prop-types
function ModelSchema({
  // eslint-disable-next-line react/prop-types
  modelToConfigure,
  onFormSubmit,
  ...rest
}) {
  const { properties, getFormValuesByProperties, handleUpdateValues } =
    useModelSchemaStore();

  const activeProperty =
    properties?.length > 0 ? properties[properties.length - 1] : null;

  const [selectedModel, setSelectedModel] = useState(
    activeProperty
      ? getFormValuesByProperties()?.properties?.params.comp.component
      : null,
  );

  const handleOnSubmit = (values) => {
    if (!activeProperty) {
      handleUpdateValues(values, onFormSubmit);
      return;
    }
    const formattedValues = {
      properties: {
        component: getFormValuesByProperties()?.properties.component,
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
    if (
      activeProperty &&
      selectedModel ===
        getFormValuesByProperties()?.properties?.params.comp.component
    ) {
      return getFormValuesByProperties()?.properties?.params?.comp?.params;
    }

    return getFormValuesByProperties();
  }, [selectedModel, activeProperty, getFormValuesByProperties]);

  useEffect(() => {
    setSelectedModel(
      activeProperty
        ? getFormValuesByProperties()?.properties?.params.comp.component
        : null,
    );
  }, [activeProperty]);

  return (
    <Stack spacing={2} sx={{ py: 2 }}>
      {/* Dropdown to select a configurable object to render a subform */}

      {Boolean(activeProperty) && (
        <>
          {properties.map((property, index) => (
            <Typography variant="overline" key={index}>
              {property}/
            </Typography>
          ))}
          <ModelSchemaSelect
            parent={getFormValuesByProperties()?.properties.component}
            selectedModel={selectedModel}
            onChange={setSelectedModel}
          />
        </>
      )}
      <ModelSchemaForm
        model={selectedModel}
        onFormSubmit={handleOnSubmit}
        initialValues={defaultValues}
      />
    </Stack>
  );
}

export default ModelSchema;
