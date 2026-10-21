import { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Box, TextField } from "@mui/material";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import Upload from "../../shared/Upload";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import {
  createDocument,
  deleteDocument,
  enqueueDocumentJob,
} from "../../../api/documents";
import { forceRefreshNow } from "../../../utils/jobPoller";
import {
  generateSequentialName,
  getNextAvailableName,
} from "../../../utils/nameGenerator";

function hasSupportedExtension(fileName, extensions) {
  if (!extensions || extensions.length === 0) return true;
  const lower = fileName.toLowerCase();
  return extensions.some((extension) => lower.endsWith(extension));
}

function stripExtension(fileName) {
  const dot = fileName.lastIndexOf(".");
  return dot > 0 ? fileName.slice(0, dot) : fileName;
}

export default function ConfigureAndUploadDocumentStep({
  selectedLoader,
  goToPrevStep,
  backHome,
  formSubmitRef,
  formHasErrors,
  existingDocuments,
  onDocumentCreated,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const { defaultName } = useMemo(
    () =>
      generateSequentialName({ base: "Document", items: existingDocuments }),
    [existingDocuments],
  );
  const [documentName, setDocumentName] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const extensions = selectedLoader?.metadata?.supported_extensions || [];
  const effectiveName = documentName.trim() || defaultName;

  const handleFileUpload = (files) => {
    const selected = Array.isArray(files) ? (files[0] ?? null) : null;
    if (selected && !hasSupportedExtension(selected.name, extensions)) {
      enqueueSnackbar(
        t("datasets:document.unsupportedExtension", {
          extensions: extensions.join(", "),
        }),
        { variant: "error" },
      );
      setFile(null);
      return;
    }
    setFile(selected);
    if (selected && !documentName.trim()) {
      setDocumentName(stripExtension(selected.name));
    }
  };

  const createWithFreeName = async (payload) => {
    try {
      return await createDocument(payload);
    } catch (error) {
      if (error.response?.status !== 409) throw error;
      const nextName = getNextAvailableName(payload.name, existingDocuments);
      setDocumentName(nextName);
      return createDocument({ ...payload, name: nextName });
    }
  };

  const handleSubmit = async () => {
    if (!file) return;
    setUploading(true);
    let created;
    try {
      created = await createWithFreeName({
        name: effectiveName,
        file_name: file.name,
        dataloader: selectedLoader.name,
        dataloader_params: formSubmitRef.current?.values || {},
      });
    } catch (error) {
      const detail = error.response?.data?.detail;
      enqueueSnackbar(
        typeof detail === "string"
          ? detail
          : t("datasets:document.createError"),
        { variant: "error" },
      );
      setUploading(false);
      return;
    }
    try {
      const job = await enqueueDocumentJob(created.id, created.name, file);
      forceRefreshNow();
      onDocumentCreated(created, job);
    } catch (error) {
      await deleteDocument(created.id).catch(() => {});
      enqueueSnackbar(t("datasets:document.enqueueError"), {
        variant: "error",
      });
      backHome();
    } finally {
      setUploading(false);
    }
  };

  return (
    <Box
      sx={{
        display: "flex",
        flexDirection: "column",
        width: "100%",
        flex: 1,
        minHeight: 0,
      }}
    >
      <Box sx={{ mb: 4 }}>
        <TextField
          label={t("datasets:document.documentName")}
          value={documentName}
          placeholder={defaultName}
          onChange={(e) => setDocumentName(e.target.value)}
          fullWidth
        />
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto" }}>
        <Upload
          onFileUpload={handleFileUpload}
          emptyUploadText={t("datasets:document.dropFile", {
            extensions: extensions.join(", "),
          })}
        />
      </Box>
      <StepperNavigationFooter
        onBack={goToPrevStep}
        onNext={handleSubmit}
        nextDisabled={!file || formHasErrors || uploading}
        nextLabel={t("common:upload")}
        loading={uploading}
      />
    </Box>
  );
}

ConfigureAndUploadDocumentStep.propTypes = {
  selectedLoader: PropTypes.object.isRequired,
  goToPrevStep: PropTypes.func.isRequired,
  backHome: PropTypes.func.isRequired,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
  formHasErrors: PropTypes.bool,
  existingDocuments: PropTypes.array,
  onDocumentCreated: PropTypes.func.isRequired,
};
