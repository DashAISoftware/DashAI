import PropTypes from "prop-types";
import { Box, Typography } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useTranslation } from "react-i18next";
import FormSchema from "../../shared/FormSchema";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import SideBar from "../../threeSectionLayout/panelContainers/SideBar";

export default function DocumentLoaderConfigBar({
  loaderName,
  formSubmitRef,
  setError,
}) {
  const { t } = useTranslation(["datasets"]);
  const theme = useTheme();

  return (
    <SideBar>
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          height: 64,
          display: "flex",
          alignItems: "center",
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("datasets:document.loaderConfiguration")}
        </Typography>
      </Box>
      <Box sx={{ flex: 1, overflowY: "auto", px: 4, pt: 2, pb: 4 }}>
        <FormSchemaContainer>
          <FormSchema
            autoSave
            model={loaderName}
            formSubmitRef={formSubmitRef}
            setError={setError}
            initialValues={{}}
            showBorder={false}
          />
        </FormSchemaContainer>
      </Box>
    </SideBar>
  );
}

DocumentLoaderConfigBar.propTypes = {
  loaderName: PropTypes.string.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
  setError: PropTypes.func.isRequired,
};
