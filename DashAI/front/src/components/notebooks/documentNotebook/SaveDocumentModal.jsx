import { useEffect, useMemo, useState } from "react";
import PropTypes from "prop-types";
import {
  Box,
  IconButton,
  List,
  ListItem,
  ListItemText,
  Modal,
  TextField,
  Typography,
} from "@mui/material";
import { Close, Transform } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import NoteBox from "../NoteBox";
import StepperNavigationFooter from "../../shared/StepperNavigationFooter";
import { generateSequentialName } from "../../../utils/nameGenerator";
import { describeItemScope } from "./documentItems";

export default function SaveDocumentModal({
  open,
  onClose,
  onSave,
  appliedConverters,
  existingDocuments,
  saving = false,
}) {
  const { t } = useTranslation(["datasets", "common"]);
  const [name, setName] = useState("");

  const { defaultName } = useMemo(
    () =>
      generateSequentialName({ base: "Document", items: existingDocuments }),
    [existingDocuments, open],
  );

  useEffect(() => {
    if (open) setName(defaultName);
  }, [open]);

  const trimmed = name.trim();
  const nameError = !trimmed
    ? t("common:nameRequired")
    : existingDocuments.some((document) => document.name === trimmed)
      ? t("datasets:document.nameExists")
      : null;

  return (
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
          outline: "none",
          display: "flex",
          flexDirection: "column",
        }}
      >
        <Box
          sx={{
            p: 2,
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            borderBottom: 1,
            borderColor: "divider",
            flexShrink: 0,
          }}
        >
          <Typography variant="h6" component="h2">
            {t("datasets:documentNotebook.saveDocumentTitle")}
          </Typography>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
            disabled={saving}
          >
            <Close />
          </IconButton>
        </Box>

        <Box
          sx={{
            px: 3,
            pt: 3,
            display: "flex",
            flexDirection: "column",
            gap: 3,
            flexShrink: 0,
          }}
        >
          <NoteBox message={t("datasets:documentNotebook.saveDocumentNote")} />
          <TextField
            fullWidth
            label={t("datasets:document.documentName")}
            value={name}
            onChange={(event) => setName(event.target.value)}
            error={Boolean(nameError)}
            helperText={nameError}
            disabled={saving}
          />
          <Typography variant="subtitle2">
            {t("datasets:label.appliedTransformations")}
          </Typography>
        </Box>

        <Box sx={{ px: 3, pb: 2, overflowY: "auto", flex: 1, minHeight: 0 }}>
          {appliedConverters.length === 0 ? (
            <Typography variant="body2" color="text.secondary">
              {t("datasets:label.noTransformationsApplied")}
            </Typography>
          ) : (
            <List dense>
              {appliedConverters.map((converter, index) => (
                <ListItem
                  key={converter.id}
                  divider={index < appliedConverters.length - 1}
                  sx={{ gap: 2 }}
                >
                  <Transform color="primary" fontSize="small" />
                  <ListItemText
                    primary={converter.converter}
                    secondary={(converter.parameters?.scope?.columns ?? [])
                      .map((column) => describeItemScope(t, column))
                      .join(" | ")}
                  />
                </ListItem>
              ))}
            </List>
          )}
        </Box>

        <Box sx={{ px: 3, pb: 3, flexShrink: 0 }}>
          <StepperNavigationFooter
            onBack={onClose}
            onNext={() => onSave(trimmed)}
            nextDisabled={Boolean(nameError) || saving}
            backLabel={t("common:cancel")}
            nextLabel={t("common:save")}
            variant="save"
          />
        </Box>
      </Box>
    </Modal>
  );
}

SaveDocumentModal.propTypes = {
  open: PropTypes.bool.isRequired,
  onClose: PropTypes.func.isRequired,
  onSave: PropTypes.func.isRequired,
  appliedConverters: PropTypes.arrayOf(PropTypes.object).isRequired,
  existingDocuments: PropTypes.arrayOf(PropTypes.object).isRequired,
  saving: PropTypes.bool,
};
