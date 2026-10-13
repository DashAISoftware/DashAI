import { useEffect, useState } from "react";
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
  MenuItem,
  TextField,
} from "@mui/material";
import Upload from "../../shared/Upload";
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

export default function RAGDocumentUpload({ open, onClose, onReady }) {
  const { t } = useTranslation(["generative", "common"]);
  const { enqueueSnackbar } = useSnackbar();
  const { documents = [], addDocumentOptimistically } =
    useDatasetsAndNotebooks();
  const [loaders, setLoaders] = useState([]);
  const [loaderName, setLoaderName] = useState("");
  const [file, setFile] = useState(null);
  const [uploading, setUploading] = useState(false);

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

  const usable = loaders.filter((loader) => acceptsFile(loader, file));

  useEffect(() => {
    if (!usable.some((loader) => loader.name === loaderName)) {
      setLoaderName(usable[0]?.name ?? "");
    }
  }, [usable, loaderName]);

  const handleClose = () => {
    setFile(null);
    setLoaderName("");
    onClose();
  };

  const handleUpload = async () => {
    setUploading(true);
    try {
      const payload = {
        name: file.name,
        file_name: file.name,
        dataloader: loaderName,
        dataloader_params: {},
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
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("generative:documentsBar.uploadTitle")}</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ display: "flex", flexDirection: "column", gap: 2 }}>
          <Upload
            onFileUpload={(files) =>
              setFile(Array.isArray(files) ? files[0] : files)
            }
            emptyUploadText={t("generative:documentsBar.uploadToData")}
          />
          <TextField
            select
            label={t("generative:documentsBar.parserLabel")}
            value={loaderName}
            onChange={(event) => setLoaderName(event.target.value)}
            disabled={usable.length === 0}
            fullWidth
          >
            {usable.map((loader) => (
              <MenuItem key={loader.name} value={loader.name}>
                {loader.display_name || loader.name}
              </MenuItem>
            ))}
          </TextField>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common:cancel")}</Button>
        <Button
          variant="contained"
          disabled={!file || !loaderName || uploading}
          onClick={handleUpload}
        >
          {t("generative:documentsBar.upload")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

RAGDocumentUpload.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onReady: PropTypes.func.isRequired,
};
