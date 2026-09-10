import PropTypes from "prop-types";
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Box,
  Typography,
  IconButton,
  Button,
} from "@mui/material";
import { Close as CloseIcon } from "@mui/icons-material";
import { useTranslation } from "react-i18next";
import SingleTestResult from "./SingleTestResult";
import PerRunResults from "./PerRunResults";

/**
 * Modal showing the full details of a saved statistical test.
 */
export default function SavedStatisticalTestResults({ open, onClose, group }) {
  const { t } = useTranslation(["models", "common"]);

  if (!group || group.length === 0) return null;

  const head = group[0];
  const title = head.name || head.test_name;
  const isBatch = group.length > 1;

  // Map each stored batch row to the {id, name, resp} shape PerRunResults wants.
  const perRunData = isBatch
    ? group.map((row) => {
        const runId = (row.run_ids && row.run_ids[0]) ?? row.id;
        const runName = Object.values(row.run_names || {})[0] || String(runId);
        return { id: runId, name: runName, resp: row };
      })
    : [];

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ bgcolor: "background.paper" }}>
        <Box
          sx={{
            display: "flex",
            alignItems: "flex-start",
            justifyContent: "space-between",
          }}
        >
          <Box>
            <Typography variant="h6" component="span">
              {title}
            </Typography>
            {head.name && head.test_name && (
              <Typography variant="body2" color="text.secondary">
                {head.test_name}
              </Typography>
            )}
          </Box>
          <IconButton
            onClick={onClose}
            size="small"
            sx={{ color: "text.secondary" }}
          >
            <CloseIcon />
          </IconButton>
        </Box>
      </DialogTitle>

      <DialogContent dividers sx={{ bgcolor: "background.paper" }}>
        {head.description && (
          <Typography
            variant="body1"
            color="text.secondary"
            sx={{ mb: 1.5, fontStyle: "italic" }}
          >
            {head.description}
          </Typography>
        )}

        {isBatch ? (
          <PerRunResults results={perRunData} />
        ) : (
          <SingleTestResult result={head} />
        )}
      </DialogContent>

      <DialogActions sx={{ p: 2, bgcolor: "background.paper" }}>
        <Button variant="outlined" onClick={onClose}>
          {t("common:close", "Cerrar")}
        </Button>
      </DialogActions>
    </Dialog>
  );
}

SavedStatisticalTestResults.propTypes = {
  open: PropTypes.bool,
  onClose: PropTypes.func.isRequired,
  group: PropTypes.arrayOf(PropTypes.object),
};
