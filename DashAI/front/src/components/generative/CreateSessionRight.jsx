import { Box, Typography } from "@mui/material";
import { useTranslation } from "react-i18next";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import ComponentDetailsPanel from "../custom/ComponentDetailsPanel";
import FormSchemaRenderFields from "../shared/FormSchemaRenderFields";
import { useTheme } from "@mui/material/styles";
import { useCreateSession } from "./CreateSessionContext";

export default function CreateSessionRight() {
  const { t } = useTranslation(["generative", "common"]);
  const theme = useTheme();
  const { step, selectedModel, formik, processedProperties } =
    useCreateSession();

  if (step === 0) {
    return (
      <Box
        data-tour="component-details-panel"
        sx={{ height: "100%", display: "flex", flexDirection: "column" }}
      >
        <ComponentDetailsPanel
          component={selectedModel}
          categoryKey="task_display_name"
        />
      </Box>
    );
  }

  return (
    <SideBar data-tour="model-parameters">
      {/* Title */}
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          height: 64,
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("common:modelParameters")}
        </Typography>
      </Box>

      {/* Content */}
      {Object.keys(processedProperties).length === 0 ? (
        <Box
          sx={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 4,
          }}
        >
          <Typography variant="body2" color="text.secondary" textAlign="center">
            {t("generative:label.modelHasNoParameters")}
          </Typography>
        </Box>
      ) : (
        <Box sx={{ flex: 1, overflowY: "auto", pt: 4, px: 4, pb: 10 }}>
          <FormSchemaRenderFields
            modelSchema={processedProperties}
            formik={formik}
            autoSave={false}
            handleUpdateSchema={(updatedValues) => {
              formik.setValues((prev) => ({ ...prev, ...updatedValues }));
            }}
            onFormSubmit={formik.handleSubmit}
            setError={(error) => console.error(error)}
            errorsMessage={formik.errors || {}}
            spacing={4}
          />
        </Box>
      )}
    </SideBar>
  );
}
