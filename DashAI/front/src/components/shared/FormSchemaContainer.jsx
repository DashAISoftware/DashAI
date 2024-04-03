/* eslint-disable react/prop-types */
import React from "react";
import { FormSchemaProvider } from "../../contexts/schema";

const FormSchemaContainer = ({ children }) => {
  return <FormSchemaProvider>{children}</FormSchemaProvider>;
};

export default FormSchemaContainer;
