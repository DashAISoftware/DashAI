import React from "react";
import PropTypes from "prop-types";
import { FormSchemaProvider } from "../../contexts/schema";

const FormSchemaContainer = ({ children }) => {
  return <FormSchemaProvider>{children}</FormSchemaProvider>;
};

FormSchemaContainer.propTypes = {
  children: PropTypes.node.isRequired,
};

export default FormSchemaContainer;
