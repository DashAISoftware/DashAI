import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useFormik } from "formik";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import {
  createGenerativeSession,
  getRelatedComponents,
} from "../../api/generativeTask";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../utils/nameGenerator";
import {
  buildYupSchema,
  formatTaskNameForSession,
  preprocessSchema,
} from "./utils";
import { useGenerative } from "./GenerativeContext";
import { isStandaloneTask } from "./standaloneEntryPoints";

const CreateSessionContext = createContext(null);

export const useCreateSession = () => useContext(CreateSessionContext);

export function CreateSessionProvider({ children }) {
  const navigate = useNavigate();
  const { modelName } = useParams();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["generative", "common"]);
  const { tasks, sessions: existingSessions, setSessions } = useGenerative();

  const step = modelName ? 1 : 0;
  const [models, setModels] = useState([]);
  const [loadingModels, setLoadingModels] = useState(true);
  const [selectedModel, setSelectedModel] = useState(null);
  const [submitting, setSubmitting] = useState(false);

  // Load all generative models grouped by their compatible task. Exposed as
  // refetchModels so callers (e.g. an inline download control) can refresh the
  // list when a model's downloaded state changes. Re-fetches when language
  // changes so display_name/description are translated.
  const loadModels = useCallback(() => {
    if (!tasks || tasks.length === 0) return Promise.resolve();
    // Tasks with their own entry point are reached from the module landing, so
    // their models must not appear in this gallery. The backend marks them.
    const galleryTasks = tasks.filter((task) => !isStandaloneTask(task));
    setLoadingModels(true);
    return Promise.all(
      galleryTasks.map((task) =>
        getRelatedComponents(task.name).then((components) =>
          components.map((c) => ({
            ...c,
            task_name: task.name,
            task_display_name: task.display_name || task.name,
          })),
        ),
      ),
    )
      .then((perTaskLists) => {
        // Deduplicate by model name (a model may appear under several tasks).
        const seen = new Set();
        const flat = [];
        perTaskLists.flat().forEach((m) => {
          if (seen.has(m.name)) return;
          seen.add(m.name);
          flat.push(m);
        });
        setModels(flat);
      })
      .catch((err) => {
        console.error("Failed to load generative models", err);
        enqueueSnackbar(t("generative:error.failedToLoadModels"), {
          variant: "error",
        });
      })
      .finally(() => {
        setLoadingModels(false);
      });
  }, [tasks, enqueueSnackbar, t]);

  useEffect(() => {
    loadModels();
  }, [loadModels]);

  const processedProperties = useMemo(
    () =>
      selectedModel?.schema?.properties
        ? preprocessSchema(selectedModel.schema.properties)
        : {},
    [selectedModel],
  );

  const validationSchema = useMemo(
    () =>
      Object.keys(processedProperties).length > 0
        ? buildYupSchema(processedProperties)
        : null,
    [processedProperties],
  );

  const formik = useFormik({
    initialValues: { name: "", description: "" },
    validationSchema,
    enableReinitialize: false,
    validate: (values) => {
      const errors = {};
      if (!values.name || values.name.trim() === "") {
        errors.name = t("generative:error.nameRequired");
      }
      return errors;
    },
    onSubmit: async (values) => {
      if (!selectedModel) return;
      setSubmitting(true);
      try {
        let effectiveName = values.name;
        let created;
        try {
          created = await createGenerativeSession({
            name: effectiveName,
            description: values.description,
            task_name: selectedModel.task_name,
            model_name: selectedModel.name,
            parameters: values,
          });
        } catch (createError) {
          if (createError?.response?.status === 409) {
            effectiveName = getNextAvailableName(
              effectiveName,
              existingSessions,
            );
            formik.setFieldValue("name", effectiveName);
            created = await createGenerativeSession({
              name: effectiveName,
              description: values.description,
              task_name: selectedModel.task_name,
              model_name: selectedModel.name,
              parameters: { ...values, name: effectiveName },
            });
          } else {
            throw createError;
          }
        }
        setSessions((prev) => [...prev, created]);
        enqueueSnackbar(t("generative:message.sessionCreatedSuccess"), {
          variant: "success",
        });
        navigate(`/app/generative/sessions/${created.id}`);
      } catch (error) {
        console.error("Error creating session:", error);
        enqueueSnackbar(t("generative:error.failedToCreateSession"), {
          variant: "error",
        });
      } finally {
        setSubmitting(false);
      }
    },
  });

  // When a model is selected, seed formik with its parameter defaults and a
  // freshly computed default session name. Computing the name here (rather than
  // in an effect) avoids the render-ordering race where the "fill empty name"
  // effect fires before resetForm has cleared the previous model's name.
  const handleSelectModel = useCallback(
    (model) => {
      setSelectedModel(model);
      const props = model?.schema?.properties
        ? preprocessSchema(model.schema.properties)
        : {};
      const paramDefaults = Object.keys(props).reduce((acc, key) => {
        acc[key] = props[key].placeholder ?? "";
        return acc;
      }, {});
      const { defaultName } = generateSequentialName({
        base: `${formatTaskNameForSession(model.task_name)}_Session`,
        items: existingSessions,
        getName: (session) => session.name,
        filter: (session) => session.task_name === model.task_name,
      });
      formik.resetForm({
        values: {
          name: defaultName,
          description: "",
          ...paramDefaults,
        },
      });
    },
    [existingSessions],
  );

  // A model whose download was removed can no longer be used to create a
  // session, so it must not stay selected.
  const isUnavailable = (model) =>
    Boolean(model?.metadata?.requires_download) && !model?.downloaded;

  // Sync selectedModel from URL param on load and after language-triggered
  // model refetch so display_name / description reflect the active language.
  // If the URL points at a model that is no longer downloaded, drop back to
  // the model selection step.
  useEffect(() => {
    if (!modelName || models.length === 0) return;
    const match = models.find((m) => m.name === modelName);
    if (!match) return;
    if (isUnavailable(match)) {
      setSelectedModel(null);
      navigate("/app/generative/sessions/new");
    } else {
      handleSelectModel(match);
    }
  }, [modelName, models]);

  // An undownloaded model may stay selected so its description is visible and
  // it can be downloaded inline; the Next button gates on the download status.
  // Only drop the selection if the model disappears from the list entirely.
  useEffect(() => {
    if (!selectedModel) return;
    const match = models.find((m) => m.name === selectedModel.name);
    if (!match) setSelectedModel(null);
  }, [models]);

  const handleNext = () => {
    if (step === 0 && selectedModel)
      navigate(`/app/generative/sessions/new/${selectedModel.name}`);
  };

  const handleBack = () => {
    if (step === 1) navigate("/app/generative/sessions/new");
    else navigate("/app/generative");
  };

  const handleCreate = () => {
    formik.submitForm();
  };

  // Flip a single model's downloaded flag in place. Used when an inline
  // download/delete finishes so the list updates without a full refetch
  // (which would swap in the loading spinner and reset the scroll position).
  const markModelDownloaded = useCallback((name, isDownloaded) => {
    setModels((prev) =>
      prev.map((m) =>
        m.name === name ? { ...m, downloaded: isDownloaded } : m,
      ),
    );
  }, []);

  const value = {
    step,
    models,
    loadingModels,
    refetchModels: loadModels,
    markModelDownloaded,
    selectedModel,
    handleSelectModel,
    formik,
    processedProperties,
    submitting,
    handleNext,
    handleBack,
    handleCreate,
  };

  return (
    <CreateSessionContext.Provider value={value}>
      {children}
    </CreateSessionContext.Provider>
  );
}
