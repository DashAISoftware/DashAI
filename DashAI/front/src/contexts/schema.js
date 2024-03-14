import React, { createContext, useContext, useState } from "react";
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

  const getFormValuesByProperties = () => {
    if (!properties.length) return formValues;

    let formValuesByProperties = { ...formValues };

    for (const property of properties) {
      formValuesByProperties = formValuesByProperties[property];
    }

    return formValuesByProperties;
  };

  const handleUpdateValues = (values, onSubmit) => {
    if (!properties.length) {
      setFormValues(values);
      onSubmit && onSubmit(values);
      return;
    }

    setFormValues((prevObj) => {
      let formValuesByProperties = prevObj;

      for (let i = 0; i < properties.length - 1; i++) {
        formValuesByProperties = formValuesByProperties[properties[i]];
      }

      formValuesByProperties[properties[properties.length - 1]] = values;
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

  return {
    formValues,
    properties,
    addProperty,
    removeLastProperty,
    getFormValuesByProperties,
    handleUpdateValues,
  };
};
