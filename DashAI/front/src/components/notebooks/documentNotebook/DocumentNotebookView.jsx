import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import { Box, Button, Divider, Tooltip } from "@mui/material";
import { Add } from "@mui/icons-material";
import { useNavigate } from "react-router-dom";
import { useSnackbar } from "notistack";
import { useTranslation } from "react-i18next";
import NotebookView from "../notebook/NotebookView";
import DocumentItemsPanel from "./DocumentItemsPanel";
import SaveDocumentModal from "./SaveDocumentModal";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { createDocumentFromNotebook } from "../../../api/documents";

const FINISHED = 3;
const ERROR = 4;

export default function DocumentNotebookView({ notebook }) {
  const { t } = useTranslation(["datasets", "common"]);
  const navigate = useNavigate();
  const { enqueueSnackbar } = useSnackbar();
  const { documents, fetchDocuments } = useDatasetsAndNotebooks();
  const { columnTypes, setItemSelection, explorersAndConverters } =
    useExplorersAndConverters();
  const [saveOpen, setSaveOpen] = useState(false);
  const [saving, setSaving] = useState(false);

  const converters = useMemo(
    () => explorersAndConverters.filter((item) => item.type === "converter"),
    [explorersAndConverters],
  );
  const converterRunning = converters.some(
    (item) => item.status !== FINISHED && item.status !== ERROR,
  );

  const documentColumns = useMemo(
    () =>
      Object.fromEntries(
        Object.entries(columnTypes || {}).filter(([, info]) => info?.kinds),
      ),
    [columnTypes],
  );

  useEffect(() => () => setItemSelection(null), [setItemSelection]);

  const handleSave = async (name) => {
    setSaving(true);
    try {
      const created = await createDocumentFromNotebook(name, notebook.id);
      setSaveOpen(false);
      enqueueSnackbar(
        t("datasets:documentNotebook.saveDocumentSuccess", { name }),
        { variant: "success" },
      );
      await fetchDocuments();
      navigate(`/app/data/documents/${created.id}`);
    } catch (error) {
      console.error("Failed to save the notebook document:", error);
      enqueueSnackbar(
        error?.response?.data?.detail ||
          t("datasets:documentNotebook.saveDocumentError"),
        { variant: "error" },
      );
    } finally {
      setSaving(false);
    }
  };

  const saveButton = (
    <Tooltip
      title={
        converterRunning ? t("datasets:documentNotebook.saveDocumentWait") : ""
      }
    >
      <span>
        <Button
          variant="contained"
          size="small"
          endIcon={<Add />}
          disabled={converterRunning || saving}
          onClick={() => setSaveOpen(true)}
          sx={{
            fontSize: "0.7rem",
            px: 3,
            py: 1,
            textTransform: "uppercase",
            minWidth: "auto",
          }}
        >
          {t("datasets:documentNotebook.saveAsNewDocument")}
        </Button>
      </span>
    </Tooltip>
  );

  return (
    <Box
      sx={{ display: "flex", flexDirection: "column", height: "100%" }}
      data-notebook-container
    >
      <Box sx={{ flexShrink: 0, mt: 2, mx: 2 }}>
        <DocumentItemsPanel
          notebookId={notebook.id}
          columnTypes={documentColumns}
          version={documentColumns}
          onFilterChange={setItemSelection}
          headerAction={saveButton}
        />
      </Box>

      <Divider sx={{ my: 2 }} />

      <Box sx={{ flexGrow: 1, minHeight: 200, overflow: "auto" }}>
        <NotebookView notebook={notebook} />
      </Box>

      <SaveDocumentModal
        open={saveOpen}
        onClose={() => setSaveOpen(false)}
        onSave={handleSave}
        appliedConverters={converters.filter(
          (item) => item.status === FINISHED,
        )}
        existingDocuments={documents}
        saving={saving}
      />
    </Box>
  );
}

DocumentNotebookView.propTypes = {
  notebook: PropTypes.shape({
    id: PropTypes.number.isRequired,
    name: PropTypes.string,
    created: PropTypes.string,
    document_id: PropTypes.number,
    data_kind: PropTypes.string,
    file_path: PropTypes.string,
  }).isRequired,
};
