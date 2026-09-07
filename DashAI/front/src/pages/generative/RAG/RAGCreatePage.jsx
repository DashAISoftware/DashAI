import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  Alert,
  Box,
  Chip,
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
import DocumentSelector from "../../../components/generative/RAG/DocumentSelector";
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
  getSessionDefaults,
} from "../../../api/rag";
import { useGenerative } from "../../../components/generative/GenerativeContext";
import { useTaskDisplayName } from "../../../hooks/generative/useTaskDisplayName";
import { useThreePanelLayout } from "../../../hooks/useThreePanelsLayout";
import { ThreePanelLayoutContext } from "../../../components/threeSectionLayout/panels/ThreePanelLayoutContext";
import { FormSchemaProvider } from "../../../contexts/schema";
import { generateSequentialName } from "../../../utils/nameGenerator";
import { getApiErrorMessage } from "../../../utils/apiError";

/**
 * Minimal RAG session creation: a name, some documents, and a model.
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
  const [documentIds, setDocumentIds] = useState([]);
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [defaults, setDefaults] = useState(null);
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

  // The defaults preview comes from the same endpoint the backend applies on
  // create, so what the user reads here is what the session will actually get.
  useEffect(() => {
    let cancelled = false;
    getSessionDefaults()
      .then((data) => {
        if (!cancelled) setDefaults(data);
      })
      .catch((error) => {
        console.error("Failed to load session defaults:", error);
      });
    return () => {
      cancelled = true;
    };
  }, []);

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

  const handleDocumentSelectionChange = useCallback((selectedDocs) => {
    setDocumentIds(selectedDocs.map((doc) => doc.id));
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
    documentIds.length > 0 &&
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
          documents: documentIds,
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

  const defaultsSummary = defaults
    ? [
        defaults.chunking_model?.display_name,
        defaults.retriever_model?.display_name,
        defaults.prompt?.display_name,
      ].filter(Boolean)
    : [];

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
              handleNewSessionButton={() => navigate("/app/generative/rag")}
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

              <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto", pb: 2 }}>
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
                      {t("generative:rag.setup.selectDocuments")}
                    </Typography>
                    <DocumentSelector
                      selectedIds={documentIds}
                      onSelect={handleDocumentSelectionChange}
                    />
                  </Box>

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
                        searchPlaceholder={t("generative:label.searchModels")}
                      />
                    )}
                  </Box>

                  {defaultsSummary.length > 0 && (
                    <Alert severity="info" icon={false}>
                      <Typography variant="body2" sx={{ mb: 1 }}>
                        {t("generative:rag.create.defaultsNotice")}
                      </Typography>
                      <Stack
                        direction="row"
                        spacing={1}
                        flexWrap="wrap"
                        useFlexGap
                      >
                        {defaultsSummary.map((label) => (
                          <Chip key={label} label={label} size="small" />
                        ))}
                      </Stack>
                    </Alert>
                  )}
                </Stack>
              </Box>

              <StepperNavigationFooter
                onBack={() => navigate("/app/generative/rag")}
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
