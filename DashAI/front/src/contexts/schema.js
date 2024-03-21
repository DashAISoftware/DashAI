import React, { createContext, useContext, useMemo, useState } from "react";
// Create the ModelSchema context
const ModelSchemaContext = createContext();

// Create the ModelSchema provider
// eslint-disable-next-line react/prop-types
export const ModelSchemaProvider = ({ children }) => {
  // Define the default values for the form
  const defaultValues = {
    // Add your default form values here
  };

  // Set up state to store the form values
  const [formValues, setFormValues] = useState(defaultValues);
  const [properties, setProperties] = useState([]);

  // Define any other functions or state variables you need

  // Create the context value object
  const contextValue = {
    formValues,
    setFormValues,
    properties,
    setProperties,
    // Add any other values or functions you want to expose to consumers
  };

  // Render the provider with the context value and children components
  return (
    <ModelSchemaContext.Provider value={contextValue}>
      {children}
    </ModelSchemaContext.Provider>
  );
};

// Custom hook to obtain the state
export const useModelSchemaStore = () => {
  const { formValues, setFormValues, properties, setProperties } =
    useContext(ModelSchemaContext);

  const valuesByProperties = useMemo(() => {
    if (!properties.length) return formValues;

    let formValuesByProperties = { ...formValues };

    for (const property of properties) {
      if (property.key in formValuesByProperties) {
        formValuesByProperties = formValuesByProperties[property.key];
      } else {
        formValuesByProperties =
          formValuesByProperties.properties.params.comp.params[property.key];
      }
    }

    return formValuesByProperties;
  }, [JSON.stringify(formValues), properties]);

  const handleUpdateValues = (values, onSubmit) => {
    if (!properties.length) {
      setFormValues(values);
      onSubmit && onSubmit(values);
      return;
    }

    setFormValues((prevObj) => {
      let formValuesByProperties = prevObj;

      for (const property of properties) {
        if (property.key in formValuesByProperties) {
          if (property.key === properties[properties.length - 1].key) {
            formValuesByProperties[property.key] = values;
          } else {
            formValuesByProperties = formValuesByProperties[property.key];
          }
        } else {
          if (property.key === properties[properties.length - 1].key) {
            formValuesByProperties.properties.params.comp.params[property.key] =
              values;
          } else {
            formValuesByProperties =
              formValuesByProperties.properties.params.comp.params[
                property.key
              ];
          }
        }
      }
      return { ...prevObj };
    });
    removeLastProperty();
  };

  const addProperty = (property) => {
    setProperties([...properties, property]);
  };

  const removeLastProperty = () => {
    setProperties(properties.slice(0, properties.length - 1));
  };

  const propertyData = useMemo(() => {
    const activeProperty = properties.length > 0;

    if (!activeProperty) {
      return {
        selected: null,
        parent: null,
        model: null,
        params: null,
      };
    }

    const data = valuesByProperties?.properties;
    return {
      selected:
        properties.length > 0 ? properties[properties.length - 1] : null,
      parent: data?.component,
      model: data?.params.comp.component,
      params: data?.params.comp.params,
    };
  }, [properties, valuesByProperties]);

  return {
    formValues,
    properties,
    propertyData,
    valuesByProperties,
    addProperty,
    removeLastProperty,
    handleUpdateValues,
  };
};
