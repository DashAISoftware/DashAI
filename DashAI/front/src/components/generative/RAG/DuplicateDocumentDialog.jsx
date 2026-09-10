import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Typography,
} from "@mui/material";
import PropTypes from "prop-types";
import { useTranslation } from "react-i18next";

/**
 * Confirmation dialog shown when the user uploads a file that already exists.
 * Lists the affected sessions and warns that fitted models will be deleted.
 *
 * @param {object}   props
 * @param {boolean}  props.open - Whether the dialog is visible.
 * @param {Array}    props.affectedSessions - [{id, name}] sessions using the document.
 * @param {function} props.onCancel - Close without forcing the update.
 * @param {function} props.onConfirm - Force the update (re-upload with force=true).
 * @returns {JSX.Element}
 */
export default function DuplicateDocumentDialog({
  open,
  affectedSessions = [],
  onCancel,
  onConfirm,
}) {
  const { t } = useTranslation("generative");

  return (
    <Dialog open={open} onClose={onCancel} maxWidth="sm" fullWidth>
      <DialogTitle>{t("rag.documents.duplicate.title")}</DialogTitle>
      <DialogContent>
        <DialogContentText>
          {t("rag.documents.duplicate.message")}
        </DialogContentText>
        {affectedSessions.length > 0 ? (
          <>
            <Typography variant="subtitle2" sx={{ mt: 2 }}>
              {t("rag.documents.duplicate.affectedSessions")}
            </Typography>
            <Box component="ul" sx={{ mt: 0, mb: 1, pl: 2.5 }}>
              {affectedSessions.map((session) => (
                <Typography key={session.id} component="li" variant="body2">
                  {session.name}
                </Typography>
              ))}
            </Box>
          </>
        ) : (
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            {t("rag.documents.duplicate.noAffectedSessions")}
          </Typography>
        )}
        <Typography
          variant="body2"
          color="warning.main"
          sx={{ mt: 2, fontWeight: 500 }}
        >
          {t("rag.documents.duplicate.warning")}
        </Typography>
      </DialogContent>
      <DialogActions>
        <Button onClick={onCancel}>
          {t("rag.documents.duplicate.cancel")}
        </Button>
        <Button variant="contained" color="primary" onClick={onConfirm}>
          {t("rag.documents.duplicate.confirm")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

DuplicateDocumentDialog.propTypes = {
  open: PropTypes.bool.isRequired,
  affectedSessions: PropTypes.arrayOf(
    PropTypes.shape({
      id: PropTypes.oneOfType([PropTypes.string, PropTypes.number]),
      name: PropTypes.string,
    }),
  ),
  onCancel: PropTypes.func.isRequired,
  onConfirm: PropTypes.func.isRequired,
};
