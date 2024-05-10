import React from "react";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import { useFormSchemaStore } from "../../contexts/schema";

/**
 * This component is the breadcrumbs for the form schema
 */

function FormSchemaBreadScrumbs() {
  const { properties, removeLastProperty } = useFormSchemaStore();

  const handleRemoveLastProperty = (index) => {
    removeLastProperty(properties.length - 1 - index);
  };

  const linkedProperties = properties
    .slice(0, properties.length - 1)
    .map((property, index) => (
      <Link
        underline="hover"
        color="inherit"
        href="#"
        key={"breadcrumb-" + property?.key}
        onClick={() => handleRemoveLastProperty(index)}
      >
        {property?.label}
      </Link>
    ));

  return (
    <Breadcrumbs maxItems={2} aria-label="breadcrumb">
      {linkedProperties}
      <Typography color="text.primary">
        {properties[properties.length - 1]?.label}
      </Typography>
    </Breadcrumbs>
  );
}

export default FormSchemaBreadScrumbs;
