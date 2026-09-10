import { Stack } from "@mui/material";
import React, { useCallback, useEffect, useMemo, useState } from "react";
import { useFormSchemaStore } from "../../contexts/schema";
import FormSchemaBreadScrumbs from "./FormSchemaBreadScrumbs";
import FormSchema from "./FormSchema";
import FormSchemaModelSelect from "./FormSchemaModelSelect";
import PropTypes from "prop-types";

/**
 * This component is a form schema with a selected model
 * @param {string} modelToConfigure - The model to configure
 * @param {object} initialValues - The initial values of the form
 * @param {function} onFormSubmit - The function to submit the form
 * @param {function} onCancel - The function to cancel the form
 */

function FormSchemaWithSelectedModel({
  modelToConfigure,
  initialValues,
  onFormSubmit,
  onCancel,
  saveButtonText,
  hideButtons,
  onValuesChange = () => {},
}) {
  const {
    formValues,
    properties,
    propertyData,
    valuesByProperties,
    removeLastProperty,
    setErrorForm,
  } = useFormSchemaStore();

  const [selectedModel, setSelectedModel] = useState(
    modelToConfigure || propertyData?.model,
  );

  const selectedProperty = Boolean(propertyData?.selected);

  const defaultValues = useMemo(() => {
    if (selectedProperty) {
      if (propertyData.params) {
        return propertyData.params;
      } else return null;
    }

    return initialValues ?? valuesByProperties;
  }, [
    selectedProperty,
    propertyData.params,
    initialValues,
    valuesByProperties,
  ]);

  useEffect(() => {
    if (propertyData.model) {
      setSelectedModel(propertyData.model);
    } else {
      setSelectedModel(modelToConfigure);
    }
  }, [propertyData.model, propertyData.params, modelToConfigure]);

  return (
    <Stack
      spacing={4}
      sx={{
        pt: 4,
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      {Boolean(propertyData?.parent) && (
        <>
          <FormSchemaBreadScrumbs rootLabel={modelToConfigure} />
          <FormSchemaModelSelect
            parent={propertyData.parent}
            selectedModel={selectedModel}
            onChange={setSelectedModel}
          />
        </>
      )}

      <FormSchema
        model={selectedModel}
        initialValues={defaultValues}
        onFormSubmit={() => onFormSubmit(formValues)}
        setError={setErrorForm}
        saveButtonText={saveButtonText}
        hideButtons={hideButtons}
        onValuesChange={() => onValuesChange(formValues)}
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

FormSchemaWithSelectedModel.propTypes = {
  modelToConfigure: PropTypes.string,
  initialValues: PropTypes.object,
  onFormSubmit: PropTypes.func.isRequired,
  onCancel: PropTypes.func.isRequired,
  saveButtonText: PropTypes.string,
  hideButtons: PropTypes.bool,
  onValuesChange: PropTypes.func,
};

export default FormSchemaWithSelectedModel;
