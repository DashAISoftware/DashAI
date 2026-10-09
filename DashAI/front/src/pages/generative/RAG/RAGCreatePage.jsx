import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  Box,
  CircularProgress,
  Stack,
  TextField,
  Typography,
} from "@mui/material";
import ModuleContainer from "../../../components/layout/ModuleContainer";
import LeftPanel from "../../../components/threeSectionLayout/panels/LeftPanel";
import CenterPanel from "../../../components/threeSectionLayout/panels/CenterPanel";
import SessionBar from "../../../components/generative/SessionBar";
import StepperNavigationFooter from "../../../components/shared/StepperNavigationFooter";
import ComponentSelector from "../../../components/custom/ComponentSelector";
import RAGBreadcrumbs from "../../../components/generative/RAG/RAGBreadcrumbs";
import {
  useCredentialStatuses,
  getComponentCredentialState,
} from "../../../components/credentials/credentialStatus";
import {
  RAG_MODEL_NAME,
  RAG_TASK_NAME,
  createRAGSession,
  getGeneratorComponents,
} from "../../../api/rag";
import { useGenerative } from "../../../components/generative/GenerativeContext";
import { useTaskDisplayName } from "../../../hooks/generative/useTaskDisplayName";
import { useThreePanelLayout } from "../../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { FormSchemaProvider } from "../../../contexts/schema";
import { generateSequentialName } from "../../../utils/nameGenerator";
import { getApiErrorMessage } from "../../../utils/apiError";

/**
 * The RAG entry point: create a session from a name and a model.
 *
 * This is what `/app/generative/rag` renders, so arriving from the hub puts
 * the cursor straight in the form. Existing sessions are listed on the left.
 *
 * Documents are uploaded into the session once it exists, so there is nothing
 * to pick here; everything else the pipeline needs has a backend default the
 * session view can change.
 *
 * Chunking, retrieval and the prompt template are filled in by the backend and
 * stay editable in the session view, so creating a session is three decisions
 * rather than six.
 *
 * @returns {JSX.Element} The RAG session creation page.
 */
export default function RAGCreatePage() {
  const navigate = useNavigate();
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const threePanelLayout = useThreePanelLayout({ storageKey: "rag" });
  const { sessions, setSessions, deleteSessionById } = useGenerative();
  const ragTitle = useTaskDisplayName(RAG_TASK_NAME);

  const [name, setName] = useState("");
  const [isNameTouched, setIsNameTouched] = useState(false);
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  const { statuses, loaded: credentialsLoaded } = useCredentialStatuses();

  // Suggest a name until the user types one of their own.
  useEffect(() => {
    if (isNameTouched) return;
    const { defaultName } = generateSequentialName({
      base: "RAG_Session",
      items: sessions ?? [],
      getName: (session) => session?.name,
    });
    setName(defaultName || "RAG_Session_1");
  }, [sessions, isNameTouched]);

  useEffect(() => {
    let cancelled = false;
    getGeneratorComponents()
      .then((data) => {
        if (!cancelled) setModels(data || []);
      })
      .catch((error) => {
        console.error("Failed to load generation models:", error);
        enqueueSnackbar(t("generative:error.failedToLoadModels"), {
          variant: "error",
        });
      })
      .finally(() => {
        if (!cancelled) setLoadingModels(false);
      });
    return () => {
      cancelled = true;
    };
  }, [enqueueSnackbar, t]);

  /**
   * Flip a model's downloaded flag in place after an inline download, so the
   * list updates without a refetch that would reset the scroll position.
   * @param {object} model - The model whose state changed.
   * @param {boolean} isDownloaded - Its new download state.
   */
  const handleDownloadChange = useCallback((model, isDownloaded) => {
    setModels((prev) =>
      prev.map((m) =>
        m.name === model.name ? { ...m, downloaded: isDownloaded } : m,
      ),
    );
  }, []);

  // Read from the live list so an inline download immediately ungates Create.
  const selectedModelState = useMemo(
    () => models.find((m) => m.name === selectedModel?.name) || selectedModel,
    [models, selectedModel],
  );

  const modelUnavailable = useMemo(() => {
    if (!selectedModelState) return true;
    const needsDownload =
      Boolean(selectedModelState.metadata?.requires_download) &&
      !selectedModelState.downloaded;
    const { locked } = getComponentCredentialState(
      selectedModelState,
      statuses,
      credentialsLoaded,
    );
    return needsDownload || locked;
  }, [selectedModelState, statuses, credentialsLoaded]);

  const canCreate =
    Boolean(name.trim()) &&
    Boolean(selectedModel) &&
    !modelUnavailable &&
    !submitting;

  const handleCreate = async () => {
    if (!canCreate) return;
    setSubmitting(true);
    try {
      const created = await createRAGSession({
        name: name.trim(),
        description: "",
        task_name: RAG_TASK_NAME,
        model_name: RAG_MODEL_NAME,
        parameters: {
          generation_model: { component: selectedModel.name, params: {} },
        },
      });
      setSessions?.((prev) => [...(prev ?? []), created]);
      enqueueSnackbar(t("generative:rag.messages.success"), {
        variant: "success",
      });
      navigate(`/app/generative/rag/sessions/${created.id}`);
    } catch (error) {
      console.error("Error creating RAG session:", error);
      enqueueSnackbar(
        getApiErrorMessage(error, t("generative:error.failedToCreateSession")),
        { variant: "error" },
      );
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <FormSchemaProvider>
      <ThreePanelLayoutContext.Provider value={threePanelLayout}>
        <ModuleContainer>
          <LeftPanel data-tour="sessions-left-panel">
            <SessionBar
              sessions={sessions}
              handleSessionClick={(sessionId) =>
                navigate(`/app/generative/rag/sessions/${sessionId}`)
              }
              handleNewSessionButton={() => navigate("/app/generative")}
              handleSessionDelete={deleteSessionById}
              onToggle={threePanelLayout.handleToggleLeft}
              showSearch={false}
              title={ragTitle}
            />
          </LeftPanel>

          <CenterPanel>
            <Box
              sx={{
                display: "flex",
                flexDirection: "column",
                height: "100%",
                minHeight: 0,
                p: 4,
              }}
            >
              <RAGBreadcrumbs />
              <Box sx={{ mb: 3 }}>
                <Typography variant="h5" component="h2">
                  {t("generative:rag.create.title")}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t("generative:rag.create.subtitle")}
                </Typography>
              </Box>

              {/* pt leaves room for the name field's floating label: it sits
                  above the input's border, and a scroll container that starts
                  flush with it clips the label against the subtitle. */}
              <Box
                sx={{
                  flex: 1,
                  minHeight: 0,
                  overflowY: "auto",
                  pt: 1.5,
                  pb: 2,
                }}
              >
                <Stack spacing={4}>
                  <TextField
                    fullWidth
                    label={t("generative:rag.setup.sessionName")}
                    value={name}
                    onChange={(event) => {
                      setIsNameTouched(true);
                      setName(event.target.value);
                    }}
                    disabled={submitting}
                  />

                  <Box>
                    <Typography variant="subtitle1" sx={{ mb: 1 }}>
                      {t("generative:rag.create.selectModel")}
                    </Typography>
                    {loadingModels ? (
                      <Box
                        sx={{
                          display: "flex",
                          justifyContent: "center",
                          py: 6,
                        }}
                      >
                        <CircularProgress />
                      </Box>
                    ) : (
                      <ComponentSelector
                        components={models}
                        selected={selectedModel}
                        onSelect={setSelectedModel}
                        onDownloadChange={handleDownloadChange}
                        flat
                        showFooter={false}
                        searchPlaceholder={t("generative:label.searchModels")}
                      />
                    )}
                  </Box>
                </Stack>
              </Box>

              <StepperNavigationFooter
                onBack={() => navigate("/app/generative")}
                onNext={handleCreate}
                backDisabled={submitting}
                nextDisabled={!canCreate}
                nextLabel={t("generative:button.createSession")}
                loading={submitting}
                variant="save"
              />
            </Box>
          </CenterPanel>
        </ModuleContainer>
      </ThreePanelLayoutContext.Provider>
    </FormSchemaProvider>
  );
}
