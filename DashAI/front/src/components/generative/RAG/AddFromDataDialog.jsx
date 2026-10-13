import { useMemo, useState } from "react";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";
import {
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Typography,
} from "@mui/material";
import SearchBar from "../../threeSectionLayout/SearchBar";
import { useDatasetsAndNotebooks } from "../../custom/contexts/DatasetsAndNotebooksContext";
import { DOCUMENT_STATUS } from "../../../hooks/datasets/useDocuments";

export default function AddFromDataDialog({
  open,
  onClose,
  attachedIds,
  onConfirm,
}) {
  const { t } = useTranslation(["generative", "datasets", "common"]);
  const { documents = [] } = useDatasetsAndNotebooks();
  const [selected, setSelected] = useState([]);
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const needle = query.trim().toLowerCase();
    return documents.filter(
      (doc) => !needle || doc.name.toLowerCase().includes(needle),
    );
  }, [documents, query]);

  const toggle = (id) =>
    setSelected((previous) =>
      previous.includes(id)
        ? previous.filter((value) => value !== id)
        : [...previous, id],
    );

  const secondaryLabel = (doc) => {
    if (attachedIds.has(doc.id))
      return t("generative:documentsBar.alreadyAttached");
    if (doc.status !== DOCUMENT_STATUS.FINISHED)
      return t("generative:documentsBar.stillProcessing");
    return doc.file_type?.toUpperCase();
  };

  const handleClose = () => {
    setSelected([]);
    setQuery("");
    onClose();
  };

  const handleConfirm = async () => {
    const ids = selected;
    handleClose();
    await onConfirm(ids);
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="sm" fullWidth>
      <DialogTitle>{t("generative:documentsBar.addFromDataTitle")}</DialogTitle>
      <DialogContent dividers>
        <Box sx={{ mb: 2 }}>
          <SearchBar
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            onClear={() => setQuery("")}
            placeholder={t("generative:documentsBar.searchPlaceholder")}
          />
        </Box>
        {visible.length === 0 ? (
          <Typography variant="body2" color="text.secondary">
            {t("generative:documentsBar.noLibraryDocuments")}
          </Typography>
        ) : (
          <List dense disablePadding>
            {visible.map((doc) => {
              const attached = attachedIds.has(doc.id);
              const disabled =
                attached || doc.status !== DOCUMENT_STATUS.FINISHED;
              return (
                <ListItemButton
                  key={doc.id}
                  disabled={disabled}
                  onClick={() => toggle(doc.id)}
                >
                  <ListItemIcon>
                    <Checkbox
                      edge="start"
                      checked={attached || selected.includes(doc.id)}
                      disabled={disabled}
                      tabIndex={-1}
                      disableRipple
                    />
                  </ListItemIcon>
                  <ListItemText
                    primary={doc.name}
                    secondary={secondaryLabel(doc)}
                  />
                </ListItemButton>
              );
            })}
          </List>
        )}
      </DialogContent>
      <DialogActions>
        <Button onClick={handleClose}>{t("common:cancel")}</Button>
        <Button
          variant="contained"
          disabled={selected.length === 0}
          onClick={handleConfirm}
        >
          {t("generative:documentsBar.addSelected", {
            count: selected.length,
          })}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

AddFromDataDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  attachedIds: PropTypes.instanceOf(Set).isRequired,
  onConfirm: PropTypes.func.isRequired,
};
