import { useState, useEffect, useMemo, useCallback } from "react";
import {
  Modal,
  TextField,
  Box,
  Typography,
  IconButton,
  Switch,
} from "@mui/material";
import { Close } from "@mui/icons-material";
import { shouldRecommendDisableMetadata } from "../../../utils/metadataRecommendation";
import ComputeMetadataConfirmDialog from "../../datasets/ComputeMetadataConfirmDialog";
import FormSchemaFieldCard from "../../shared/FormSchemaFieldCard";
import { useSnackbar } from "notistack";
import ConverterHistoryList from "../converter/ConverterHistoryList";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import NoteBox from "../NoteBox";
import DeleteConfirmationModal from "../../threeSectionLayout/DeleteConfirmationModal";
import ItemsToDeleteList from "../converter/ItemsToDeleteList";
import { deleteConverterById } from "../../../api/converter";
import {
  getConvertersByNotebookId,
  getExplorersByNotebookId,
} from "../../../api/notebook";
import { useExplorersAndConverters } from "../context/ExplorersAndConvertersContext";
import { generateSequentialName } from "../../../utils/nameGenerator";
import { useTourContext } from "../../tour/TourProvider";
import { useTranslation } from "react-i18next";

export function SaveDatasetModal({
  open,
  onClose,
  onSaveDataset,
  appliedConverters,
  existingDatasets = [],
  notebook,
  hasNoColumns = false,
}) {
  const [name, setName] = useState("");
  const [frozenDefaultName, setFrozenDefaultName] = useState("");
  const [localConverters, setLocalConverters] = useState([]);
  const [openDeleteConfirmation, setOpenDeleteConfirmation] = useState(false);
  const [converterToDelete, setConverterToDelete] = useState(null);
  const [deleteModalContent, setDeleteModalContent] = useState("");
  const [itemsToDelete, setItemsToDelete] = useState([]);
  const [computeMetadata, setComputeMetadata] = useState(true);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const notebookColCount = notebook?.total_columns ?? 0;
  const notebookRowCount = notebook?.total_rows ?? 0;
  const exceedsThreshold = shouldRecommendDisableMetadata({
    colCount: notebookColCount,
    estRows: notebookRowCount,
  });

  const tourContext = useTourContext();
  const { enqueueSnackbar } = useSnackbar();
  const { t } = useTranslation(["datasets", "common"]);
  const { explorersAndConverters, setExplorersAndConverters } =
    useExplorersAndConverters();

  const { defaultName } = useMemo(() => {
    if (tourContext && tourContext.run) {
      return { defaultName: "Clean_Personality_Dataset" };
    }
    return generateSequentialName({
      base: "Dataset",
      items: existingDatasets,
    });
  }, [existingDatasets, open]);

  useEffect(() => {
    if (open && defaultName) {
      setFrozenDefaultName(defaultName);
      setName(defaultName);
    }
  }, [open, defaultName]);

  useEffect(() => {
    setLocalConverters(appliedConverters);
  }, [appliedConverters]);

  const fetchExplorersAndConverters = useCallback(async () => {
    if (!notebook) return;
    try {
      const [explorersData, convertersData] = await Promise.all([
        getExplorersByNotebookId(notebook.id),
        getConvertersByNotebookId(notebook.id),
      ]);
      const explorersWithType = explorersData.map((item) => ({
        ...item,
        type: "explorer",
      }));
      const convertersWithType = convertersData.map((item) => ({
        ...item,
        type: "converter",
      }));
      const merged = [...explorersWithType, ...convertersWithType].sort(
        (a, b) => new Date(a.created) - new Date(b.created),
      );
      setExplorersAndConverters(merged);
    } catch (error) {
      console.error("Failed to fetch explorers and converters:", error);
    }
  }, [notebook, setExplorersAndConverters]);

  const getItemsToDelete = useCallback(
    (converter) => {
      const converterIndex = explorersAndConverters.findIndex(
        (item) => item.id === converter.id && item.type === "converter",
      );
      if (converterIndex === -1) return [];
      return explorersAndConverters.slice(converterIndex);
    },
    [explorersAndConverters],
  );

  const handleConverterDeleteClick = useCallback(
    (converter) => {
      setConverterToDelete(converter);
      const items = getItemsToDelete(converter);
      setItemsToDelete(items);
      setDeleteModalContent(
        t("datasets:label.deleteConverterConfirmation", {
          converter: converter?.converter,
        }),
      );
      setOpenDeleteConfirmation(true);
    },
    [getItemsToDelete, t],
  );

  const handleConfirmConverterDelete = useCallback(async () => {
    if (!converterToDelete) return;
    try {
      await deleteConverterById(converterToDelete.id);
      await fetchExplorersAndConverters();
      setLocalConverters((prev) =>
        prev.filter((c) => c.id !== converterToDelete.id),
      );
      setOpenDeleteConfirmation(false);
      setConverterToDelete(null);
      setDeleteModalContent("");
      setItemsToDelete([]);
    } catch (error) {
      console.error("Failed to delete converter:", error);
    }
  }, [converterToDelete, fetchExplorersAndConverters]);

  const handleCancelDelete = useCallback(() => {
    setOpenDeleteConfirmation(false);
    setConverterToDelete(null);
    setDeleteModalContent("");
    setItemsToDelete([]);
  }, []);

  const doSubmit = (effectiveComputeMetadata) => {
    const datasetName = name.trim();
    if (!datasetName) return;
    if (existingDatasets.some((dataset) => dataset.name === datasetName)) {
      enqueueSnackbar(t("datasets:error.datasetExists"), {
        variant: "warning",
      });
      return;
    }
    onSaveDataset(datasetName, {
      compute_metadata: effectiveComputeMetadata,
    });
    handleClose();
  };

  const handleSubmit = () => {
    if (computeMetadata && exceedsThreshold) {
      setConfirmOpen(true);
      return;
    }
    doSubmit(computeMetadata);
  };

  const handleClose = () => {
    onClose();
  };

  const getNameError = () => {
    const currentName = name.trim();
    if (!currentName) {
      return t("common:nameRequired");
    }
    if (
      currentName !== frozenDefaultName &&
      existingDatasets.some((dataset) => dataset.name === currentName)
    ) {
      return t("datasets:error.datasetExists");
    }
    return null;
  };

  const nameError = getNameError();

  return (
    <>
      <Modal open={open} onClose={() => {}}>
        <Box
          sx={{
            position: "absolute",
            top: "50%",
            left: "50%",
            transform: "translate(-50%, -50%)",
            width: { xs: "90%", sm: 560 },
            maxHeight: "90vh",
            bgcolor: "background.paper",
            borderRadius: 2,
            boxShadow: 12,
            p: 0,
            outline: "none",
            display: "flex",
            flexDirection: "column",
          }}
        >
          {/* Header */}
          <Box
            sx={{
              p: 2,
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
              flexShrink: 0,
            }}
          >
            <Typography variant="h6" component="h2">
              {t("datasets:label.saveProcessedDataset")}
            </Typography>
            <IconButton
              onClick={handleClose}
              size="small"
              sx={{ color: "text.secondary" }}
            >
              <Close />
            </IconButton>
          </Box>

          {/* Static fields — always visible, never scroll */}
          <Box
            sx={{
              px: 3,
              pt: 3,
              display: "flex",
              flexDirection: "column",
              gap: 3,
              flexShrink: 0,
            }}
            data-tour="save-dataset-modal-notebook"
          >
            <NoteBox
              message={t("datasets:label.newDatasetCreatedWithTransformations")}
            />
            <TextField
              fullWidth
              label={t("datasets:label.datasetName")}
              value={name}
              onChange={(e) => setName(e.target.value)}
              variant="outlined"
              error={Boolean(nameError)}
              helperText={nameError}
            />

            <FormSchemaFieldCard
              label={t("datasets:computeMetadata.label")}
              description={t("datasets:computeMetadata.helper")}
            >
              <Box sx={{ pt: 2 }}>
                <Switch
                  checked={computeMetadata}
                  onChange={(e) => setComputeMetadata(e.target.checked)}
                  size="small"
                  name="compute_metadata"
                />
              </Box>
            </FormSchemaFieldCard>

            <Typography variant="subtitle2">
              {t("datasets:label.appliedTransformations")}
            </Typography>
          </Box>

          {/* Scrollable converter list */}
          <Box
            sx={{
              px: 3,
              pb: 2,
              overflowY: "auto",
              flex: 1,
              minHeight: 0,
            }}
          >
            {localConverters.length === 0 ? (
              <Typography variant="body2" color="text.secondary">
                {t("datasets:label.noTransformationsApplied")}
              </Typography>
            ) : (
              <ConverterHistoryList
                converters={localConverters}
                onConverterDelete={handleConverterDeleteClick}
                showDeleteButtons={true}
              />
            )}
          </Box>

          {/* Footer - always visible */}
          <Box sx={{ px: 3, pb: 3, flexShrink: 0 }}>
            {hasNoColumns && (
              <Typography
                variant="caption"
                color="error"
                sx={{ display: "block", mb: 1, textAlign: "center" }}
              >
                {t("datasets:error.cannotSaveEmptyDataset")}
              </Typography>
            )}
            <StepperNavigationFooter
              onBack={handleClose}
              onNext={handleSubmit}
              nextDisabled={Boolean(nameError) || hasNoColumns}
              backLabel={t("common:cancel")}
              nextLabel={t("common:upload")}
              variant="save"
            />
          </Box>
        </Box>
      </Modal>

      <DeleteConfirmationModal
        open={openDeleteConfirmation}
        onClose={handleCancelDelete}
        onConfirm={handleConfirmConverterDelete}
        content={
          <Box>
            <Typography>{deleteModalContent}</Typography>
            <ItemsToDeleteList items={itemsToDelete} />
          </Box>
        }
      />

      <ComputeMetadataConfirmDialog
        open={confirmOpen}
        colCount={notebookColCount}
        estRows={notebookRowCount}
        onConfirm={() => {
          setConfirmOpen(false);
          doSubmit(true);
        }}
        onCancel={() => setConfirmOpen(false)}
      />
    </>
  );
}
