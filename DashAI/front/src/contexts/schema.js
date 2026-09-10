import React, { createContext, useContext, useMemo, useState } from "react";
import {
  formattedSubform,
  getModelFromSubform,
  getParamsFromSubform,
} from "../utils/schema";
import PropTypes from "prop-types";
import { useSnackbar } from "notistack";

/**
 * This context provides the form schema state and functions,
 * such as the form values, properties, property data, and functions to update the schema
 * property data is the data of the current property being configured, if is null, then the form is at the root level
 * properties is an array of the properties that are being configuredm, if is empty, then the form is at the root level
 * formValues is the current form values, this is the object that will be sent as a parameter to the onSubmit function
 * valuesByProperties is the form values that are being configured by the properties array.
 */

// Create the FormSchema context
const FormSchemaContext = createContext();

const fallbackContextValue = {
  formValues: {},
  setFormValues: () => {},
  properties: [],
  setProperties: () => {},
  errorForm: false,
  setErrorForm: () => {},
};

// Create the FormSchema provider
export const FormSchemaProvider = ({ children }) => {
  // Define the default values for the form
  const defaultValues = {
    // Add your default form values here
  };

  // Set up state to store the form values
  const [formValues, setFormValues] = useState(defaultValues);
  const [errorForm, setErrorForm] = useState(false);
  const [properties, setProperties] = useState([]);

  // Define any other functions or state variables you need

  // Create the context value object
  const contextValue = {
    formValues,
    setFormValues,
    properties,
    setProperties,
    errorForm,
    setErrorForm,

    // Add any other values or functions you want to expose to consumers
  };

  // Render the provider with the context value and children components
  return (
    <FormSchemaContext.Provider value={contextValue}>
      {children}
    </FormSchemaContext.Provider>
  );
};

FormSchemaProvider.propTypes = {
  children: PropTypes.node.isRequired,
};

// Custom hook to obtain the state
export const useFormSchemaStore = () => {
  const context = useContext(FormSchemaContext) || fallbackContextValue;
  const {
    formValues,
    setFormValues,
    properties,
    setProperties,
    errorForm,
    ...rest
  } = context;

  const { enqueueSnackbar } = useSnackbar();

  const valuesByProperties = useMemo(() => {
    if (!properties.length) return formValues;

    let formValuesByProperties = { ...formValues };

    for (const property of properties) {
      if (!formValuesByProperties) {
        return null;
      }

      if (property.key in formValuesByProperties) {
        formValuesByProperties = formValuesByProperties[property.key];
      } else {
        if (formValuesByProperties.properties?.params?.comp?.params) {
          formValuesByProperties =
            formValuesByProperties.properties.params.comp.params[property.key];
        } else {
          return null;
        }
      }
    }

    return formValuesByProperties;
  }, [formValues, properties]);

  const handleUpdateSchema = (values, onSubmit) => {
    if (!properties.length) {
      if (onSubmit) {
        onSubmit({ ...formValues, ...values });
      }
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
        model: propertyData.model,
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
    if (errorForm) {
      enqueueSnackbar("Form with errors", { variant: "warning" });
      return;
    }

    setProperties(properties.slice(0, properties.length - removedProperties));
  };

  const getModelFromCurrentProperty = (property) => {
    if (formValues === null || !property) return null;

    //console.log("formValues", formValues);
    //console.log("properties", properties);

    if (properties.length === 0) {
      return formValues[property]
        ? getModelFromSubform(formValues[property])
        : null;
    }

    // Walk down the property chain, unwrapping each subform into its params
    // map. This must unwrap the last property too: the current view's params
    // map is what holds the field being rendered. Without unwrapping the last
    // hop, a component field nested inside another component (depth >= 2) reads
    // undefined and its select never reflects a selection.
    let params = null;
    for (const prop of properties) {
      params =
        params === null
          ? getParamsFromSubform(formValues[prop.key])
          : getParamsFromSubform(params[prop.key]);
    }

    return params && params[property]
      ? getModelFromSubform(params[property])
      : null;
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
    setFormValues,
    properties,
    propertyData,
    valuesByProperties,
    addProperty,
    removeLastProperty,
    handleUpdateSchema,
    getModelFromCurrentProperty,
    errorForm,
    ...rest,
  };
};
