import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import { useSnackbar } from "notistack";
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Typography,
} from "@mui/material";
import TuneIcon from "@mui/icons-material/Tune";
import Upload from "../../shared/Upload";
import FormSchema from "../../shared/FormSchema";
import FormSchemaContainer from "../../shared/FormSchemaContainer";
import ParserSelector from "./ParserSelector";
import { getComponents } from "../../../api/component";
import { createDocument, enqueueDocumentJob } from "../../../api/documents";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { loadsDataKind } from "../../../utils/dataKinds";
import { getApiErrorMessage } from "../../../utils/apiError";
import { startJobPolling } from "../../../utils/jobPoller";
import { getNextAvailableName } from "../../../utils/nameGenerator";

function acceptsFile(loader, file) {
  const extensions = loader?.metadata?.supported_extensions ?? [];
  return (
    !file || extensions.some((ext) => file.name.toLowerCase().endsWith(ext))
  );
}

function loaderDescription(loader) {
  return loader?.description ?? loader?.schema?.description ?? "";
}

function LoaderParameters({ loader, formSubmitRef, setError }) {
  const { t } = useTranslation(["generative", "datasets"]);

  if (!loader) {
    return (
      <Box
        sx={{
          flex: 1,
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 1,
          p: 4,
          textAlign: "center",
          color: "text.secondary",
        }}
      >
        <TuneIcon />
        <Typography variant="body2">
          {t("generative:documentsBar.selectParser")}
        </Typography>
      </Box>
    );
  }

  return (
    <Box
      sx={{
        flex: 1,
        minHeight: 0,
        display: "flex",
        flexDirection: "column",
      }}
    >
      <Box sx={{ px: 3, pt: 2.5, pb: 1, flexShrink: 0 }}>
        <Typography
          variant="overline"
          color="text.secondary"
          sx={{ display: "block", lineHeight: 2 }}
        >
          {t("datasets:document.loaderConfiguration")}
        </Typography>
      </Box>
      <Box sx={{ flex: 1, minHeight: 0, overflowY: "auto", px: 3, pb: 3 }}>
        <FormSchemaContainer>
          <FormSchema
            key={loader.name}
            autoSave
            model={loader.name}
            formSubmitRef={formSubmitRef}
            setError={setError}
            initialValues={{}}
            showBorder={false}
            hideButtons
          />
        </FormSchemaContainer>
      </Box>
    </Box>
  );
}

export default function RAGDocumentUpload({ open, onClose, onReady }) {
  const { t } = useTranslation(["generative", "datasets", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const { documents = [], addDocumentOptimistically } =
    useDatasetsAndNotebooks();
  const [loaders, setLoaders] = useState([]);
  const [loaderName, setLoaderName] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [formHasErrors, setFormHasErrors] = useState(false);
  const formSubmitRef = useRef(null);

  useEffect(() => {
    if (!open) return undefined;
    let cancelled = false;
    getComponents({ selectTypes: ["DataLoader"] })
      .then((list) => {
        if (!cancelled) {
          setLoaders(list.filter((c) => loadsDataKind(c, "document")));
        }
      })
      .catch(() => {
        if (!cancelled) setLoaders([]);
      });
    return () => {
      cancelled = true;
    };
  }, [open]);

  const isCompatible = useCallback(
    (loader) => acceptsFile(loader, file),
    [file],
  );
  const usable = useMemo(
    () => loaders.filter(isCompatible),
    [loaders, isCompatible],
  );
  const selectedLoader =
    usable.find((loader) => loader.name === loaderName) ?? null;
  const selectedDescription = loaderDescription(selectedLoader);
  const selectedExtensions =
    selectedLoader?.metadata?.supported_extensions ?? [];

  useEffect(() => {
    if (!usable.some((loader) => loader.name === loaderName)) {
      setLoaderName(usable[0]?.name ?? "");
    }
  }, [usable, loaderName]);

  useEffect(() => {
    setFormHasErrors(false);
  }, [loaderName]);

  const handleClose = () => {
    setFile(null);
    setLoaderName("");
    setFormHasErrors(false);
    onClose();
  };

  const handleUpload = async () => {
    setUploading(true);
    try {
      const payload = {
        name: file.name,
        file_name: file.name,
        dataloader: loaderName,
        dataloader_params: formSubmitRef.current?.values || {},
      };
      const created = await createDocument(payload).catch((error) => {
        if (error.response?.status !== 409) throw error;
        return createDocument({
          ...payload,
          name: getNextAvailableName(file.name, documents),
        });
      });
      const job = await enqueueDocumentJob(created.id, created.name, file);
      addDocumentOptimistically?.(created);
      enqueueSnackbar(
        t("generative:documentsBar.processingUpload", { file: created.name }),
        { variant: "info" },
      );
      startJobPolling(
        job.id,
        async () => {
          await onReady([created.id]);
        },
        () => {
          enqueueSnackbar(
            t("generative:documentsBar.uploadFailedReason", {
              file: created.name,
              reason: t("generative:documentsBar.parseFailed"),
            }),
            { variant: "error" },
          );
        },
      );
      handleClose();
    } catch (error) {
      enqueueSnackbar(
        t("generative:documentsBar.uploadFailedReason", {
          file: file.name,
          reason: getApiErrorMessage(
            error,
            t("generative:documentsBar.parseFailed"),
          ),
        }),
        { variant: "error" },
      );
    } finally {
      setUploading(false);
    }
  };

  return (
    <Dialog
      open={open}
      onClose={handleClose}
      maxWidth={false}
      fullWidth
      slotProps={{
        paper: {
          sx: {
            height: "90vh",
            maxWidth: "min(1680px, 95vw)",
            bgcolor: "background.paper",
            backgroundImage: "none",
          },
        },
      }}
    >
      <DialogTitle>{t("generative:documentsBar.uploadTitle")}</DialogTitle>
      <DialogContent
        dividers
        sx={{ p: 0, display: "flex", minHeight: 0, overflow: "hidden" }}
      >
        <Box
          sx={{
            flex: 3,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            gap: 2,
            p: 2,
            overflowY: "auto",
          }}
        >
          <ParserSelector
            loaders={loaders}
            isCompatible={isCompatible}
            selectedName={selectedLoader?.name ?? null}
            onSelect={setLoaderName}
          />
          <Upload
            onFileUpload={(files) =>
              setFile(Array.isArray(files) ? files[0] : files)
            }
            emptyUploadText={
              selectedExtensions.length > 0
                ? t("datasets:document.dropFile", {
                    extensions: selectedExtensions.join(", "),
                  })
                : t("generative:documentsBar.uploadToData")
            }
          />
          {selectedDescription && (
            <Box>
              <Typography
                variant="overline"
                color="text.secondary"
                sx={{ display: "block", lineHeight: 2, mb: 0.5 }}
              >
                {t("common:description")}
              </Typography>
              <Typography variant="subtitle2" sx={{ fontWeight: 600 }}>
                {selectedLoader.display_name || selectedLoader.name}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mt: 0.5, whiteSpace: "pre-line" }}
              >
                {selectedDescription}
              </Typography>
            </Box>
          )}
        </Box>
        <Box
          sx={{
            flex: 1,
            minWidth: 0,
            display: "flex",
            flexDirection: "column",
            borderLeft: 1,
            borderColor: "divider",
          }}
        >
          <LoaderParameters
            loader={selectedLoader}
            formSubmitRef={formSubmitRef}
            setError={setFormHasErrors}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common:cancel")}</Button>
        <Button
          variant="contained"
          disabled={!file || !selectedLoader || formHasErrors || uploading}
          onClick={handleUpload}
        >
          {t("generative:documentsBar.upload")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

LoaderParameters.propTypes = {
  loader: PropTypes.object,
  formSubmitRef: PropTypes.shape({ current: PropTypes.any }).isRequired,
  setError: PropTypes.func.isRequired,
};

RAGDocumentUpload.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onReady: PropTypes.func.isRequired,
};
