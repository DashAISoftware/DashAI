import React from "react";
import PropTypes from "prop-types";
import Breadcrumbs from "@mui/material/Breadcrumbs";
import Typography from "@mui/material/Typography";
import Link from "@mui/material/Link";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import { useFormSchemaStore } from "../../contexts/schema";

/**
 * This component is the breadcrumbs for the form schema
 * @param {string} rootLabel - Label for the root (top level) model crumb
 */

function FormSchemaBreadScrumbs({ rootLabel }) {
  const theme = useTheme();
  const { t } = useTranslation(["common"]);
  const { properties, removeLastProperty } = useFormSchemaStore();

  const handleRemoveLastProperty = (index) => {
    removeLastProperty(properties.length - 1 - index);
  };

  // Root crumb: pops every nested property to return to the top level model.
  const rootCrumb = (
    <Link
      underline="hover"
      color="inherit"
      component="button"
      key="breadcrumb-root"
      onClick={() => removeLastProperty(properties.length)}
      sx={{ background: "none", border: "none", cursor: "pointer" }}
    >
      {rootLabel || t("common:model")}
    </Link>
  );

  const linkedProperties = properties
    .slice(0, properties.length - 1)
    .map((property, index) => (
      <Link
        underline="hover"
        color="inherit"
        component="button"
        key={"breadcrumb-" + property?.key}
        onClick={() => handleRemoveLastProperty(index)}
        sx={{ background: "none", border: "none", cursor: "pointer" }}
      >
        {property?.label}
      </Link>
    ));

  return (
    <Breadcrumbs maxItems={3} aria-label="breadcrumb">
      {rootCrumb}
      {linkedProperties}
      <Typography sx={{ color: theme.palette.text.primary }}>
        {properties[properties.length - 1]?.label}
      </Typography>
    </Breadcrumbs>
  );
}

FormSchemaBreadScrumbs.propTypes = {
  rootLabel: PropTypes.string,
};

export default FormSchemaBreadScrumbs;
