import { useEffect, useState, useRef } from "react";
import { Box, Typography, Button, IconButton, Divider } from "@mui/material";
import { useTheme } from "@mui/material/styles";
import { useFormik } from "formik";
import FormSchemaRenderFields from "../shared/FormSchemaRenderFields";
import HistoryIcon from "@mui/icons-material/History";
import ParameterHistoryModal from "./SessionHistoryModal";
import { getHistoryBySessionId } from "../../api/session";
import {
  getGenerativeSession,
  getRelatedComponents,
  updateGenerativeSessionParams,
} from "../../api/generativeTask";
import { preprocessSchema, buildYupSchema } from "./utils";
import SideBar from "../threeSectionLayout/panelContainers/SideBar";
import { useTranslation } from "react-i18next";
import { useGenerative } from "./GenerativeContext";
import { useTourContext } from "../tour/TourProvider";

export default function ParamsBar({ onToggle }) {
  const {
    selectedSessionId,
    selectedTaskName: taskName,
    paramsVersion,
    setParamsVersion,
  } = useGenerative();
  const [parameters, setParameters] = useState({});
  const [historyInfoVisible, setHistoryInfoVisible] = useState(false);
  const [history, setHistory] = useState([]);

  const [selectedModel, setSelectedModel] = useState(null);
  const [validationSchema, setValidationSchema] = useState(null);
  const { t } = useTranslation(["generative", "common"]);
  const tourContext = useTourContext();
  const hasAdvancedTourRef = useRef(false);

  const getHistory = () => {
    getHistoryBySessionId(selectedSessionId).then((response) => {
      setHistory(response);
    });
  };

  useEffect(() => {
    if (!selectedSessionId) return;
    getHistory();
  }, []);

  useEffect(() => {
    if (!selectedSessionId) return;

    getGenerativeSession(selectedSessionId).then((session) => {
      setParameters(session.parameters);

      getRelatedComponents(session.task_name).then((relatedComponents) => {
        const relatedModel = relatedComponents.find(
          (component) => component.name === session.model_name,
        );

        if (relatedModel && relatedModel.schema) {
          setSelectedModel(relatedModel);
        }
      });
    });
  }, [selectedSessionId, t, paramsVersion]);

  useEffect(() => {
    if (selectedModel?.schema?.properties) {
      const processedProps = preprocessSchema(selectedModel.schema.properties);
      setValidationSchema(buildYupSchema(processedProps));
    }
  }, [selectedModel]);

  const onParamsUpdate = () => {
    setParamsVersion((prev) => prev + 1);
  };

  const handleUpdateParameters = async (updatedParams) => {
    try {
      const updatedSession = await updateGenerativeSessionParams(
        selectedSessionId,
        updatedParams,
      );
      setParameters(updatedSession.parameters);
      onParamsUpdate(updatedSession.parameters);

      // Advance tour to chat input if tour is running
      const currentTarget =
        tourContext?.steps?.[tourContext?.stepIndex]?.target;
      if (
        tourContext?.run &&
        currentTarget === '[data-tour="parameters-right-panel"]' &&
        !hasAdvancedTourRef.current
      ) {
        hasAdvancedTourRef.current = true;
        const waitForElement = () => {
          const element = document.querySelector('[data-tour="chat-input"]');
          if (element) {
            setTimeout(() => {
              tourContext.nextStep();
            }, 100);
          } else {
            setTimeout(waitForElement, 100);
          }
        };
        setTimeout(waitForElement, 100);
      }
    } catch (error) {
      console.error("Failed to update session parameters:", error);
    }
  };

  const formik = useFormik({
    initialValues: parameters,
    validationSchema,
    enableReinitialize: true,
    onSubmit: (values) => handleUpdateParameters(values),
  });

  const processedProperties = selectedModel?.schema?.properties
    ? preprocessSchema(selectedModel.schema.properties)
    : {};

  const theme = useTheme();

  return (
    <SideBar data-tour="parameters-right-panel">
      <Box
        sx={{
          p: 4,
          borderBottom: `1px solid ${theme.palette.ui.border}`,
          flexShrink: 0,
          display: "flex",
          alignItems: "center",
          justifyContent: "flex-start",
          height: 64,
        }}
      >
        <Typography variant="h6" color="text.primary">
          {t("common:modelParameters")}
        </Typography>

        {/* Parameter History Modal */}
        {selectedSessionId && (
          <IconButton
            onClick={() => {
              getHistory();
              setHistoryInfoVisible(true);
            }}
            sx={{
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <HistoryIcon
              sx={{
                color: "primary.main",
              }}
            />
          </IconButton>
        )}
      </Box>

      {selectedSessionId ? (
        <Box sx={{ flex: 1, overflowY: "auto", pt: 4 }}>
          <form onSubmit={formik.handleSubmit}>
            <Box sx={{ mr: 4, ml: 4 }}>
              {/* Render the parameter fields */}
              <FormSchemaRenderFields
                modelSchema={processedProperties}
                formik={formik}
                autoSave={false}
                handleUpdateSchema={(updatedValues) => {
                  formik.setValues((prevValues) => ({
                    ...prevValues,
                    ...updatedValues,
                  }));
                }}
                onFormSubmit={formik.handleSubmit}
                setError={(error) => console.error(error)}
                errorsMessage={formik.errors || {}}
                spacing={2}
              />
              <Box
                sx={{
                  display: "flex",
                  justifyContent: "flex-end",
                  py: 4,
                  position: "sticky",
                  bottom: 0,
                  backgroundColor: "background.box",
                }}
              >
                <Button
                  type="submit"
                  variant="contained"
                  disabled={!formik.dirty}
                >
                  {t("common:update")}
                </Button>
              </Box>
            </Box>
          </form>
        </Box>
      ) : (
        <Box
          sx={{
            flex: 1,
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            p: 4,
          }}
        >
          <Typography
            variant="body2"
            sx={{ color: "text.secondary", textAlign: "center" }}
          >
            {t("generative:label.selectSessionToViewParameters")}
          </Typography>
        </Box>
      )}

      {/* Parameter History Modal */}
      <ParameterHistoryModal
        historyChanges={history}
        open={historyInfoVisible}
        taskName={taskName}
        setOpen={setHistoryInfoVisible}
      />
    </SideBar>
  );
}
