import ExpandLessIcon from "@mui/icons-material/ExpandLess";
import ExpandMoreIcon from "@mui/icons-material/ExpandMore";
import { Collapse, IconButton } from "@mui/material";
import PropTypes from "prop-types";
import React from "react";
import { useTranslation } from "react-i18next";
import { FormCardResetProvider } from "../../contexts/FormCardContext";
import FormSchemaFieldCard from "./FormSchemaFieldCard";

/**
 * Renders an object-type field as a collapsible card.
 * The expand/collapse toggle lives in the card header.
 * Sub-fields inside the collapse are wrapped in FormCardResetProvider so their
 * FormInputWrapper tooltips remain visible.
 */
function FormSchemaFieldWithCollapse({
  name,
  label,
  description,
  errorMessage,
  children,
  defaultExpanded = false,
}) {
  const [showSection, setShowSection] = React.useState(defaultExpanded);
  const { t } = useTranslation(["common"]);

  const toggleButton = (
    <IconButton
      size="small"
      color={errorMessage ? "error" : "default"}
      aria-label={showSection ? t("common:collapse") : t("common:expand")}
      onClick={() => setShowSection((prev) => !prev)}
    >
      {showSection ? <ExpandLessIcon /> : <ExpandMoreIcon />}
    </IconButton>
  );

  return (
    <FormSchemaFieldCard
      label={label}
      paramKey={name}
      description={description}
      errorMessage={errorMessage}
      headerRight={toggleButton}
    >
      <Collapse in={showSection}>
        {/* Reset card context so sub-field FormInputWrapper tooltips are visible */}
        <FormCardResetProvider>{children}</FormCardResetProvider>
      </Collapse>
    </FormSchemaFieldCard>
  );
}

FormSchemaFieldWithCollapse.propTypes = {
  name: PropTypes.string,
  label: PropTypes.string.isRequired,
  description: PropTypes.string,
  errorMessage: PropTypes.string,
  children: PropTypes.node,
  defaultExpanded: PropTypes.bool,
};

export default FormSchemaFieldWithCollapse;
