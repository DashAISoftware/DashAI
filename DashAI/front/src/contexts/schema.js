import React, { createContext, useContext, useMemo, useState } from "react";
import { formattedSubform } from "../utils/schema";
// Create the FormSchema context
const FormSchemaContext = createContext();

// Create the FormSchema provider
// eslint-disable-next-line react/prop-types
export const FormSchemaProvider = ({ children }) => {
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
    <FormSchemaContext.Provider value={contextValue}>
      {children}
    </FormSchemaContext.Provider>
  );
};

// Custom hook to obtain the state
export const useFormSchemaStore = () => {
  const { formValues, setFormValues, properties, setProperties } =
    useContext(FormSchemaContext);

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

  const handleUpdateSchema = (values) => {
    if (!properties.length) {
      setFormValues((prev) => ({ ...prev, ...values }));
      return;
    }

    let formattedValues;

    // Check if the values are already formatted
    if (values?.properties) {
      formattedValues = values;
    } else {
      formattedValues = formattedSubform({
        parent: propertyData.parent,
        Form: propertyData.Form,
        params: { ...propertyData.params, ...values },
      });
    }

    setFormValues((prevObj) => {
      let formValuesByProperties = prevObj;

      for (const property of properties) {
        if (property.key in formValuesByProperties) {
          if (property.key === properties[properties.length - 1].key) {
            formValuesByProperties[property.key] = formattedValues;
          } else {
            formValuesByProperties = formValuesByProperties[property.key];
          }
        } else {
          if (property.key === properties[properties.length - 1].key) {
            formValuesByProperties.properties.params.comp.params[property.key] =
              formattedValues;
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
  };

  const addProperty = (property) => {
    setProperties([...properties, property]);
  };

  const removeLastProperty = (removedProperties = 1) => {
    setProperties(properties.slice(0, properties.length - removedProperties));
  };

  const propertyData = useMemo(() => {
    const activeProperty = properties.length > 0;

    if (!activeProperty) {
      return {
        selected: null,
        parent: null,
        Form: null,
        params: null,
      };
    }

    const data = valuesByProperties?.properties;
    return {
      selected:
        properties.length > 0 ? properties[properties.length - 1] : null,
      parent: data?.component,
      Form: data?.params.comp.component,
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
    handleUpdateSchema,
  };
};
