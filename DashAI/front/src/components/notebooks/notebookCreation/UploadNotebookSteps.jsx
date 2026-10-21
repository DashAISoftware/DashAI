import { useState, useMemo, useEffect, useRef } from "react";
import {
  Typography,
  TextField,
  Box,
  ToggleButton,
  ToggleButtonGroup,
} from "@mui/material";
import TableChartOutlinedIcon from "@mui/icons-material/TableChartOutlined";
import ArticleOutlinedIcon from "@mui/icons-material/ArticleOutlined";
import { useFormik } from "formik";
import DatasetAutocomplete from "./DatasetAutocomplete";
import DocumentAutocomplete from "./DocumentAutocomplete";
import { createNotebook } from "../../../api/notebook";
import { useSnackbar } from "notistack";
import NoteBox from "../NoteBox";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import { generateSequentialName } from "../../../utils/nameGenerator";

const SOURCE_KIND_DATASET = "dataset";
const SOURCE_KIND_DOCUMENT = "document";

export default function UploadNotebookSteps({
  backHome,
  datasets,
  documents = [],
  handleNotebookCreated,
  existingNotebooks = [],
  preselectedDatasetId = null,
  preselectedDocumentId = null,
}) {
  const [sourceKind, setSourceKind] = useState(
    preselectedDocumentId ? SOURCE_KIND_DOCUMENT : SOURCE_KIND_DATASET,
  );
  const [selectedDataset, setSelectedDataset] = useState(
    preselectedDatasetId
      ? datasets.find((d) => d.id === preselectedDatasetId) || null
      : null,
  );
  const [selectedDocument, setSelectedDocument] = useState(
    preselectedDocumentId
      ? documents.find((d) => d.id === preselectedDocumentId) || null
      : null,
  );
  const { enqueueSnackbar } = useSnackbar();
  const tourContext = useTourContext();
  const { t } = useTranslation(["datasets", "common"]);

  const { defaultName } = useMemo(
    () =>
      generateSequentialName({ base: "Notebook", items: existingNotebooks }),
    [existingNotebooks],
  );

  const lastAutoFilledRef = useRef(null);

  const formik = useFormik({
    initialValues: {
      name: "",
      description: "",
    },
    enableReinitialize: true,
    onSubmit: async (values) => {
      try {
        const notebookName = values.name.trim();

        if (!notebookName) {
          return;
        }

        const source =
          sourceKind === SOURCE_KIND_DOCUMENT
            ? { document_id: selectedDocument.id }
            : { dataset_id: selectedDataset.id };

        const notebookData = {
          name: notebookName,
          description: values.description,
          ...source,
        };

        const createdNotebook = await createNotebook(notebookData);

        enqueueSnackbar(t("datasets:message.notebookCreated"), {
          variant: "success",
        });
        handleNotebookCreated(createdNotebook);
        if (tourContext?.run) {
          tourContext.completeTour();
          sessionStorage.setItem("startNotebookTour", "true");
        }
      } catch (error) {
        console.error("Error creating notebook:", error);
        enqueueSnackbar(t("datasets:error.errorCreatingNotebook"), {
          variant: "error",
        });
      }
    },
  });

  useEffect(() => {
    if (!defaultName) return;
    const currentName = formik.values.name.trim();
    if (!currentName || currentName === lastAutoFilledRef.current) {
      formik.setFieldValue("name", defaultName);
      lastAutoFilledRef.current = defaultName;
    }
  }, [defaultName]);

  const nameError = formik.values.name.trim() ? null : t("common:nameRequired");
  const isDocumentSource = sourceKind === SOURCE_KIND_DOCUMENT;
  const selectedSource = isDocumentSource ? selectedDocument : selectedDataset;
  const isValid = selectedSource && !nameError;

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        height: "100%",
        minHeight: 0,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <Typography variant="h5" component="h1">
          {t("datasets:label.createNewNotebook")}
        </Typography>
        <Typography variant="body2" color="text.secondary">
          {t("datasets:label.createNewNotebookDescription")}
        </Typography>
      </Box>

      <Box
        sx={{
          flex: 1,
          minHeight: 0,
          overflowY: "auto",
          pt: 2,
          display: "flex",
          flexDirection: "column",
          gap: 4,
        }}
      >
        <NoteBox
          className="notebook-note-box"
          data-tour="notebook-note-box"
          message={
            isDocumentSource
              ? t("datasets:documentNotebook.creationNote")
              : t("datasets:label.notebookCreationNote")
          }
        />

        <TextField
          fullWidth
          label={t("datasets:label.notebookName")}
          name="name"
          value={formik.values.name}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          error={Boolean(formik.touched.name && nameError)}
          helperText={formik.touched.name ? nameError : ""}
        />

        <TextField
          fullWidth
          multiline
          minRows={3}
          label={t("datasets:label.notebookDescription")}
          name="description"
          value={formik.values.description}
          onChange={formik.handleChange}
          onBlur={formik.handleBlur}
          error={Boolean(
            formik.touched.description && formik.errors.description,
          )}
          helperText={formik.touched.description && formik.errors.description}
        />

        <Box sx={{ display: "flex", flexDirection: "column", gap: 1 }}>
          <Typography variant="caption" color="text.secondary">
            {t("datasets:documentNotebook.sourceKind")}
          </Typography>
          <ToggleButtonGroup
            value={sourceKind}
            exclusive
            size="small"
            onChange={(_event, next) => next && setSourceKind(next)}
          >
            <ToggleButton
              value={SOURCE_KIND_DATASET}
              sx={{ gap: 1, textTransform: "none" }}
            >
              <TableChartOutlinedIcon fontSize="small" />
              {t("datasets:documentNotebook.sourceDataset")}
            </ToggleButton>
            <ToggleButton
              value={SOURCE_KIND_DOCUMENT}
              sx={{ gap: 1, textTransform: "none" }}
            >
              <ArticleOutlinedIcon fontSize="small" />
              {t("datasets:documentNotebook.sourceDocument")}
            </ToggleButton>
          </ToggleButtonGroup>
        </Box>

        {isDocumentSource ? (
          <DocumentAutocomplete
            documents={documents}
            selectedDocument={selectedDocument}
            setSelectedDocument={setSelectedDocument}
          />
        ) : (
          <DatasetAutocomplete
            datasets={datasets}
            selectedDataset={selectedDataset}
            setSelectedDataset={setSelectedDataset}
          />
        )}
      </Box>

      <StepperNavigationFooter
        onBack={backHome}
        onNext={formik.handleSubmit}
        nextDisabled={!isValid}
        nextLabel={t("datasets:button.createNotebook")}
        nextDataTour={tourContext?.run ? "create-notebook-button" : undefined}
      />
    </Box>
  );
}
